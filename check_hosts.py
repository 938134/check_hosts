#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用多线路 hosts 生成器
https://github.com/938134/check_hosts
"""

# ======================== 可配置区域 ========================
CONFIG = {
    "default_country": "JP",  # 默认线路
    "max_concurrent": 5,  # 最大并发
    "ping_port": 80,  # 延迟测试端口
    "ping_timeout": 2,  # 延迟测试超时(秒)
    "dns_timeout": 10,  # DNS 查询超时(秒)
    "template_file": "README_template.md",  # 模板
    "readme_file": "README.md",  # 输出文档
    "hosts_file": "hosts",  # 输出 hosts
}

# 国家/地区代码 ↔ dnschecker 路径映射
COUNTRY_MAP = {
    "HK": "hk",  # 香港 - 最稳/最低延迟，默认首选
    "JP": "jp",  # 日本 - 华东/华北最快
    "SG": "sg",  # 新加坡 - 华南/移动友好
    "KR": "kr",  # 韩国 - 联通/东北表现佳
    "TW": "tw",  # 台湾 - 东南沿海可选
    "US": "us",  # 美国 - 冷备/大带宽廉价
    "DE": "de",  # 德国 - 欧洲备用
}
# ==========================================================

import argparse
import asyncio
import httpx
import random
import time
import os
import sys
from datetime import datetime, timezone, timedelta

# ---------- 工具 ----------
def load_template():
    tpl = os.path.join(os.path.dirname(__file__), CONFIG["template_file"])
    if not os.path.exists(tpl):
        print(f"模板文件不存在: {tpl}")
        sys.exit(1)
    with open(tpl, "r", encoding="utf-8") as f:
        return f.read()

def write_readme(ipv4_content: str, ipv6_content: str, update_time: str):
    content = load_template().format(
        ipv4_hosts_str=ipv4_content,
        ipv6_hosts_str=ipv6_content,
        update_time=update_time,
    )
    readme_path = os.path.join(os.path.dirname(__file__), CONFIG["readme_file"])
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("\n~README.md 已更新~")

def write_hosts(hosts_content: str):
    hosts_path = os.path.join(os.path.dirname(__file__), CONFIG["hosts_file"])
    with open(hosts_path, "w", encoding="utf-8") as f:
        f.write(hosts_content)
    print(f"\n~最新Hosts {hosts_path} 已更新~")

# ---------- 核心 ----------
class HostsBuilder:
    def __init__(self, country_code: str):
        self.country_code = country_code.upper()
        if self.country_code not in COUNTRY_MAP:
            print(f"不支持的国家/地区: {country_code}，支持列表: {list(COUNTRY_MAP.keys())}")
            sys.exit(1)
        self.country_path = COUNTRY_MAP[self.country_code]
        self.udp = random.random() * 1000 + (int(time.time() * 1000) % 1000)
        self.csrf_token = None

    async def get_csrf_token(self):
        url = f"https://dnschecker.org/ajax_files/gen_csrf.php?udp={self.udp}"
        headers = {
            "referer": f"https://dnschecker.org/country/{self.country_path}/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                token = resp.json().get("csrf")
                if token:
                    print(f"获取CSRF Token: {token}")
                    self.csrf_token = token
                    return token
            print("无法获取 CSRF Token")
            return None

    async def fetch_ips(self, domain: str, record_type: str):
        url = (
            f"https://dnschecker.org/ajax_files/api/336/{record_type}/{domain}"
            f"?dns_key=country&dns_value={self.country_path}&v=0.36&cd_flag=1&upd={self.udp}"
        )
        headers = {
            "csrftoken": self.csrf_token,
            "referer": f"https://dnschecker.org/country/{self.country_path}/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        }
        async with httpx.AsyncClient(timeout=CONFIG["dns_timeout"]) as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if "result" in data and "ips" in data["result"]:
                        ips_str = data["result"]["ips"]
                        return [ip.strip() for ip in ips_str.split("<br />") if ip.strip()]
                return []
            except httpx.ReadTimeout:
                print(f"DNS 查询超时: {domain}")
                return []

    async def ping_ip(self, ip: str):
        try:
            start = time.time()
            async with httpx.AsyncClient() as client:
                await client.get(f"http://{ip}:{CONFIG['ping_port']}", timeout=CONFIG["ping_timeout"])
            latency = (time.time() - start) * 1000
            return ip, latency
        except Exception:
            return ip, float("inf")

    async def find_fastest(self, ips):
        if not ips:
            return None
        tasks = [self.ping_ip(ip) for ip in ips]
        results = await asyncio.gather(*tasks)
        fastest = min(results, key=lambda x: x[1])
        print("\n延迟排行:")
        for ip, latency in sorted(results, key=lambda x: x[1]):
            print(f"  {ip:<30} {latency:>7.2f}ms")
        return fastest[0] if fastest[1] != float("inf") else None

    async def process_domain(self, domain, semaphore):
        async with semaphore:
            print(f"正在处理: {domain}")
            ipv4_ips = await self.fetch_ips(domain, "A")
            ipv6_ips = await self.fetch_ips(domain, "AAAA")
            fastest_ipv4 = await self.find_fastest(ipv4_ips) if ipv4_ips else None
            fastest_ipv6 = await self.find_fastest(ipv6_ips) if ipv6_ips else None
            return domain, fastest_ipv4, fastest_ipv6

    async def run(self):
        print(f"开始检测最快IP —— 线路: {self.country_code}({self.country_path})")
        if not await self.get_csrf_token():
            sys.exit(1)

        domains_file = os.path.join(os.path.dirname(__file__), "domains.txt")
        if not os.path.exists(domains_file):
            print(f"域名文件不存在: {domains_file}")
            sys.exit(1)
        with open(domains_file, "r", encoding="utf-8") as f:
            domains = [line.strip() for line in f if line.strip()]

        sem = asyncio.Semaphore(CONFIG["max_concurrent"])
        results = await asyncio.gather(*[self.process_domain(d, sem) for d in domains])

        ipv4_list = [(ip, dom) for dom, ip, _ in results if ip]
        ipv6_list = [(ip, dom) for dom, _, ip in results if ip]

        update_time = datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0).isoformat()
        ipv4_block = "\n".join(f"{ip:<27} {dom}" for ip, dom in ipv4_list) or "# No IPv4 entries"
        ipv6_block = "\n".join(f"{ip:<50} {dom}" for ip, dom in ipv6_list) or "# No IPv6 entries"

        hosts_content = HOSTS_TEMPLATE.format(
            ipv4_content=ipv4_block,
            ipv6_content=ipv6_block,
            update_time=update_time,
        )
        write_readme(ipv4_block, ipv6_block, update_time)
        write_hosts(hosts_content)

# ---------- 入口 ----------
async def async_main():
    parser = argparse.ArgumentParser(description="多线路 hosts 自动生成器")
    parser.add_argument(
        "-c", "--country", default=CONFIG["default_country"],
        help=f"国家/地区代码，默认: {CONFIG['default_country']}，可选: {list(COUNTRY_MAP.keys())}"
    )
    args = parser.parse_args()
    builder = HostsBuilder(args.country)
    await builder.run()

if __name__ == "__main__":
    asyncio.run(async_main())
