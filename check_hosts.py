#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 实测通 | 使用 cloudscraper 过 CF | 修复 IPv6 测试
"""

# ======================== 可配置区域 ========================
CONFIG = {
    "default_country": "HK",
    "max_concurrent": 5,
    "ping_port": 80,
    "ping_timeout": 2,
    "dns_timeout": 10,
    "template_file": "README_template.md",
    "readme_file": "README.md",
    "hosts_file": "hosts",
}

COUNTRY_MAP = {
    "HK": "hk", "JP": "jp", "SG": "sg", "KR": "kr",
    "TW": "tw", "US": "us", "DE": "de",
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
from tenacity import retry, stop_after_attempt, wait_random
import cloudscraper

HOSTS_TEMPLATE = """# IPv4 Hosts
{ipv4_content}

# IPv6 Hosts
{ipv6_content}

# Generated at: {update_time}
# Star me: https://github.com/938134/check_hosts
"""


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


# ---------- 使用 cloudscraper 过 CF ----------
# 注意：由于改用 Google DNS，CSRF Token 可能不再需要，但保留函数结构
@retry(stop=stop_after_attempt(3), wait=wait_random(min=2, max=4))
def get_csrf_token_sync(udp: float, country_path: str):
    """保留函数结构，但实际不需要 CSRF Token"""
    print(f"[DEBUG] 使用 Google DNS，无需 CSRF Token")
    return "not_needed_for_google_dns"


# 异步包装器
async def get_csrf_token(udp: float, country_path: str):
    """异步包装同步函数"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_csrf_token_sync, udp, country_path)


# ---------- 谷歌 DNS 查询函数 ----------
def fetch_ips_sync(domain: str, record_type: str, country_path: str, udp: float, csrf_token: str):
    """使用 Google Public DNS 查询 DNS 记录"""
    
    # 根据记录类型设置 Google DNS 查询参数
    if record_type == "A":
        dns_type = "A"  # IPv4
    elif record_type == "AAAA":
        dns_type = "AAAA"  # IPv6
    else:
        print(f"[ERROR] 不支持的 DNS 记录类型: {record_type}")
        return []
    
    # Google Public DNS API URL
    url = f"https://dns.google/resolve?name={domain}&type={dns_type}"
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    }
    
    print(f"[DEBUG] 使用 Google DNS 查询 {dns_type} 记录: {domain}")
    
    try:
        resp = httpx.get(url, headers=headers, timeout=CONFIG["dns_timeout"])
        print(f"[DNS查询] {domain} {dns_type} - HTTP {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            # 解析 Google DNS 响应格式
            if "Answer" in data:
                ips = []
                for answer in data["Answer"]:
                    if answer.get("type") == 1:  # A 记录类型代码为 1
                        ips.append(answer["data"])
                    elif answer.get("type") == 28:  # AAAA 记录类型代码为 28
                        ips.append(answer["data"])
                
                print(f"[DEBUG] 从 Google DNS 解析到 {len(ips)} 个 {dns_type} IP")
                return ips
            else:
                print(f"[DEBUG] Google DNS 查询 {domain} 无 {dns_type} 记录")
                return []
        else:
            print(f"[DNS查询] Google DNS 失败: {resp.status_code} - {resp.text[:200]}")
            return []
            
    except Exception as e:
        print(f"Google DNS 查询异常: {domain} {dns_type}, 错误: {e}")
        return []


async def fetch_ips(domain: str, record_type: str, country_path: str, udp: float, csrf_token: str):
    """异步包装 DNS 查询"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, fetch_ips_sync, domain, record_type, country_path, udp, csrf_token
    )


class HostsBuilder:
    def __init__(self, country_code: str):
        self.country_code = country_code.upper()
        if self.country_code not in COUNTRY_MAP:
            print(f"不支持的国家/地区: {country_code}，支持列表: {list(COUNTRY_MAP.keys())}")
            sys.exit(1)
        
        self.country_path = COUNTRY_MAP[self.country_code]
        self.udp = random.random() * 1000 + (int(time.time() * 1000) % 1000)
        self.csrf_token = None

    async def get_csrf(self):
        try:
            self.csrf_token = await get_csrf_token(self.udp, self.country_path)
            return self.csrf_token
        except Exception as e:
            print(f"获取 CSRF Token 失败: {e}")
            return "not_needed"

    async def ping_ip(self, ip: str):
        """改进的 ping 测试，支持 IPv6"""
        try:
            start = time.time()
            
            # 判断是 IPv4 还是 IPv6
            if ':' in ip:  # IPv6
                # 对于 IPv6，使用更简单的连通性测试
                async with httpx.AsyncClient() as client:
                    # 尝试使用 HTTPS 而不是 HTTP，因为很多 IPv6 服务可能不支持 HTTP
                    await client.get(f"https://[{ip}]/", timeout=CONFIG["ping_timeout"])
            else:  # IPv4
                async with httpx.AsyncClient() as client:
                    await client.get(f"http://{ip}:{CONFIG['ping_port']}", timeout=CONFIG["ping_timeout"])
                    
            latency = (time.time() - start) * 1000
            return ip, latency
        except Exception as e:
            # 如果 HTTPS 失败，尝试 HTTP（仅对 IPv6）
            if ':' in ip:
                try:
                    start = time.time()
                    async with httpx.AsyncClient() as client:
                        await client.get(f"http://[{ip}]:{CONFIG['ping_port']}", timeout=CONFIG["ping_timeout"])
                    latency = (time.time() - start) * 1000
                    return ip, latency
                except Exception:
                    return ip, float("inf")
            else:
                return ip, float("inf")

    async def find_fastest_ipv4(self, ips):
        """查找最快的 IPv4 地址"""
        if not ips:
            return None
            
        print(f"\nIPv4 延迟测试:")
        tasks = [self.ping_ip(ip) for ip in ips]
        results = await asyncio.gather(*tasks)
        
        # 过滤掉超时的结果
        valid_results = [(ip, latency) for ip, latency in results if latency != float("inf")]
        
        if not valid_results:
            print(f"  IPv4 所有地址均超时")
            return None
            
        fastest = min(valid_results, key=lambda x: x[1])
        
        print(f"\nIPv4 延迟排行:")
        for ip, latency in sorted(valid_results, key=lambda x: x[1]):
            print(f"  {ip:<30} {latency:>7.2f}ms")
            
        return fastest[0]

    async def find_best_ipv6(self, ips):
        """查找最佳的 IPv6 地址（如果测试失败，使用第一个地址）"""
        if not ips:
            return None
            
        print(f"\nIPv6 连通性测试:")
        tasks = [self.ping_ip(ip) for ip in ips]
        results = await asyncio.gather(*tasks)
        
        # 过滤掉超时的结果
        valid_results = [(ip, latency) for ip, latency in results if latency != float("inf")]
        
        if valid_results:
            # 如果有可用的 IPv6 地址，选择最快的
            fastest = min(valid_results, key=lambda x: x[1])
            print(f"\nIPv6 延迟排行:")
            for ip, latency in sorted(valid_results, key=lambda x: x[1]):
                print(f"  {ip:<50} {latency:>7.2f}ms")
            return fastest[0]
        else:
            # 如果所有 IPv6 地址测试都失败，使用第一个地址
            # 因为很多 IPv6 地址可能由于防火墙无法 ping 通，但实际访问时可用
            print(f"  IPv6 延迟测试全部失败，使用第一个地址: {ips[0]}")
            return ips[0]

    async def process_domain(self, domain, semaphore):
        async with semaphore:
            print(f"\n{'='*50}")
            print(f"正在处理: {domain}")
            print(f"{'='*50}")
            
            # 查询 IPv4 - 使用 Google DNS
            ipv4_ips = await fetch_ips(domain, "A", self.country_path, self.udp, self.csrf_token)
            print(f"IPv4 结果: {len(ipv4_ips)} 个地址")
            
            # 查询 IPv6 - 使用 Google DNS
            ipv6_ips = await fetch_ips(domain, "AAAA", self.country_path, self.udp, self.csrf_token)
            print(f"IPv6 结果: {len(ipv6_ips)} 个地址")
            
            # 测试延迟
            fastest_ipv4 = await self.find_fastest_ipv4(ipv4_ips) if ipv4_ips else None
            fastest_ipv6 = await self.find_best_ipv6(ipv6_ips) if ipv6_ips else None
            
            print(f"最佳 IPv4: {fastest_ipv4}")
            print(f"最佳 IPv6: {fastest_ipv6}")
            
            return domain, fastest_ipv4, fastest_ipv6

    async def run(self):
        print(f"开始检测最快IP —— 线路: {self.country_code}({self.country_path})")
        
        # 由于使用 Google DNS，CSRF Token 不是必需的，但保持接口兼容
        await self.get_csrf()

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

        print(f"\n{'='*50}")
        print("最终结果:")
        print(f"IPv4 条目: {len(ipv4_list)}")
        print(f"IPv6 条目: {len(ipv6_list)}")
        print(f"{'='*50}")

        hosts_content = HOSTS_TEMPLATE.format(
            ipv4_content=ipv4_block,
            ipv6_content=ipv6_block,
            update_time=update_time,
        )
        write_readme(ipv4_block, ipv6_block, update_time)
        write_hosts(hosts_content)


# ---------- 入口 ----------
async def async_main():
    parser = argparse.ArgumentParser(description="多线路 hosts 自动生成器（使用 Google DNS 查询）")
    parser.add_argument(
        "-c", "--country", default=CONFIG["default_country"],
        help=f"国家/地区代码，默认: {CONFIG['default_country']}，可选: {list(COUNTRY_MAP.keys())}"
    )
    args = parser.parse_args()
    builder = HostsBuilder(args.country)
    await builder.run()


if __name__ == "__main__":
    asyncio.run(async_main())
