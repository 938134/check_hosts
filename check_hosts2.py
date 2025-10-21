#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_hosts.py  (ipip.net 线路版)
仅保留 IPv4，逻辑最简，直接请求 ipip.net 取最优 IP。
"""

import asyncio
import httpx
import re
import json
import os
import sys
import time
import random
from datetime import datetime, timezone, timedelta

Hosts_TEMPLATE = """
# IPv4 Hosts
{ipv4_content}

# Generated at: {update_time}
# Star me: https://github.com/938134/check_hosts
"""

# -------------------- 工具函数 --------------------
def write_file(ipv4_hosts_content: str, update_time: str) -> bool:
    """渲染 README.md"""
    template_path = os.path.join(os.path.dirname(__file__), "README_template.md")
    if not os.path.exists(template_path):
        print(f"模板缺失：{template_path}")
        return False
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read().format(ipv4_hosts_str=ipv4_hosts_content, update_time=update_time)
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("\n~README.md 已更新~")
    return True

def write_host_file(hosts_content: str, filename: str) -> None:
    output_path = os.path.join(os.path.dirname(__file__), filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(hosts_content)
    print(f"\n~最新 hosts 已写入：{output_path}")

# -------------------- ipip.net 获取最优 IP --------------------
async def get_fastest_ip_from_ipip(domain: str) -> str:
    """返回延迟最低的 IPv4；失败返回 None"""
    url = f"https://tools.ipip.net/ping.php?v=4&a=send&host={domain}&dns=&method=icmp&area[]=china"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://tools.ipip.net/ping.php"
    }
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"[IPIP] HTTP {resp.status_code}  domain={domain}")
                return None
        except Exception as e:
            print(f"[IPIP] 请求异常 domain={domain}  {e}")
            return None

    # 提取所有 call_ping({...})
    pattern = re.compile(r'parent\.call_ping\(({.*?})\);', re.DOTALL)
    matches = pattern.findall(resp.text)
    best_ip, min_rtt = None, float("inf")
    for m in matches:
        try:
            data = json.loads(m)
            ip = data.get("ip")
            rtt = float(data.get("rtt_avg", float("inf")))
            if ip and rtt < min_rtt:
                min_rtt, best_ip = rtt, ip
        except:
            continue
    if best_ip:
        print(f"[IPIP] 最优 IP →  {best_ip:<15} 延迟={min_rtt:.2f}ms  ({domain})")
    else:
        print(f"[IPIP] 未解析到有效 IP  ({domain})")
    return best_ip

# -------------------- 主流程 --------------------
async def process_domain(domain: str) -> tuple[str, str]:
    fastest_ipv4 = await get_fastest_ip_from_ipip(domain)
    return domain, fastest_ipv4

async def main():
    domains_file = os.path.join(os.path.dirname(__file__), "domains.txt")
    if not os.path.exists(domains_file):
        print(f"域名列表缺失：{domains_file}")
        sys.exit(1)
    with open(domains_file, "r", encoding="utf-8") as f:
        domains = [line.strip() for line in f if line.strip()]

    semaphore = asyncio.Semaphore(5)          # 并发限制
    async def sem_task(d):
        async with semaphore:
            return await process_domain(d)
    results = await asyncio.gather(*(sem_task(d) for d in domains))

    ipv4_lines = []
    for domain, ip in results:
        if ip:
            ipv4_lines.append(f"{ip:<27} {domain}")
    update_time = datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0).isoformat()

    ipv4_content = "\n".join(ipv4_lines) if ipv4_lines else "# No IPv4 entries"
    hosts_str = Hosts_TEMPLATE.format(ipv4_content=ipv4_content, update_time=update_time)

    write_file(ipv4_content, update_time)
    write_host_file(hosts_str, "hosts")

if __name__ == "__main__":
    asyncio.run(main())
