#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_hosts.py  (ipip.net 双栈版)
同时获取 IPv4/IPv6 并选最优
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

Hosts_TEMPLATE = """# IPv4 Hosts
{ipv4_content}

# IPv6 Hosts
{ipv6_content}

# Generated at: {update_time}
# Star me: https://github.com/938134/check_hosts
"""

# ------------------------------------------------------
def write_file(ipv4_hosts_content: str, ipv6_hosts_content: str, update_time: str) -> bool:
    """渲染 README.md"""
    template_path = os.path.join(os.path.dirname(__file__), "README_template.md")
    if not os.path.exists(template_path):
        print(f"模板缺失：{template_path}")
        return False
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read().format(
            ipv4_hosts_str=ipv4_hosts_content,
            ipv6_hosts_str=ipv6_hosts_content,
            update_time=update_time
        )
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

# ------------------------------------------------------
async def get_best_ip(stack: str, domain: str) -> str:
    """
    stack: 'v4' | 'v6'
    返回最优 IP；失败返回 None
    """
    url = (
        f"https://tools.ipip.net/ping.php?v={stack[-1]}&a=send&host={domain}"
        f"&dns=&method=icmp&area[]=china"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://tools.ipip.net/ping.php"
    }
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"[IPIP] HTTP {resp.status_code}  {stack.upper()}  domain={domain}")
                return None
        except Exception as e:
            print(f"[IPIP] 请求异常  {stack.upper()}  domain={domain}  {e}")
            return None

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
        print(f"[IPIP] 最优 {stack.upper()} →  {best_ip:<39} 延迟={min_rtt:>7.2f}ms  ({domain})")
    else:
        print(f"[IPIP] 未解析到有效 {stack.upper()}  ({domain})")
    return best_ip

# ------------------------------------------------------
async def process_domain(domain: str) -> tuple[str, str, str]:
    """返回 (domain, best_v4, best_v6)"""
    best_v4 = await get_best_ip("v4", domain)
    best_v6 = await get_best_ip("v6", domain)
    return domain, best_v4, best_v6

# ------------------------------------------------------
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

    ipv4_lines, ipv6_lines = [], []
    for domain, v4, v6 in results:
        if v4:
            ipv4_lines.append(f"{v4:<39} {domain}")
        if v6:
            ipv6_lines.append(f"{v6:<39} {domain}")

    update_time = datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0).isoformat()
    ipv4_content = "\n".join(ipv4_lines) if ipv4_lines else "# No IPv4 entries"
    ipv6_content = "\n".join(ipv6_lines) if ipv6_lines else "# No IPv6 entries"

    hosts_str = Hosts_TEMPLATE.format(
        ipv4_content=ipv4_content,
        ipv6_content=ipv6_content,
        update_time=update_time
    )

    write_file(ipv4_content, ipv6_content, update_time)
    write_host_file(hosts_str, "hosts")

# ------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
