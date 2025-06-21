import asyncio
import httpx
import random
import time
from datetime import datetime, timezone, timedelta
import os
import sys

Hosts_TEMPLATE = """
# IPv4 Hosts
{ipv4_content}

# IPv6 Hosts
{ipv6_content}

# Generated at: {update_time}
# Star me: https://github.com/938134/check_hosts
"""

def write_file(ipv4_hosts_content: str, ipv6_hosts_content: str, update_time: str) -> bool:
    """更新 README.md 文件"""
    # 读取 README_template.md 模板内容
    template_path = os.path.join(os.path.dirname(__file__), "README_template.md")
    if not os.path.exists(template_path):
        print(f"错误：模板文件 {template_path} 不存在！")
        return False
    with open(template_path, "r", encoding="utf-8") as template_file:
        template_content = template_file.read()
    
    # 替换模板中的占位符
    updated_content = template_content.format(
        ipv4_hosts_str=ipv4_hosts_content,
        ipv6_hosts_str=ipv6_hosts_content,
        update_time=update_time
    )
    
    # 写入 README.md 文件
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    with open(readme_path, "w", encoding="utf-8") as readme_file:
        readme_file.write(updated_content)
    print("\n~README.md 已更新~")
    return True

def write_host_file(hosts_content: str, filename: str) -> None:
    output_path = os.path.join(os.path.dirname(__file__), filename)
    with open(output_path, "w", encoding='utf-8') as output_fb:
        output_fb.write(hosts_content)
    print(f"\n~最新Hosts {output_path} 地址已更新~")

async def get_csrf_token(udp: float) -> str:
    """获取 CSRF Token"""
    url = f'https://dnschecker.org/ajax_files/gen_csrf.php?udp={udp}'
    headers = {
        'referer': 'https://dnschecker.org/country/cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            csrf_token = response.json().get("csrf")
            if csrf_token:
                print(f"获取到的 CSRF Token: {csrf_token}")
                return csrf_token
            else:
                print("无法获取 CSRF Token")
                return None
        else:
            print(f"请求失败，HTTP状态码: {response.status_code}")
            return None

async def get_domain_ips(domain: str, csrf_token: str, udp: float, record_type: str) -> list:
    """获取域名的 IPv4 或 IPv6 地址"""
    url = f"https://dnschecker.org/ajax_files/api/363/{record_type}/{domain}?dns_key=country&dns_value=cn&v=0.36&cd_flag=1&upd={udp}"
    headers = {
        "csrftoken": csrf_token,
        "referer": "https://dnschecker.org/country/kr/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                if "result" in response_data and "ips" in response_data["result"]:
                    ips_str = response_data["result"]["ips"]
                    if "<br />" in ips_str:
                        return [ip.strip() for ip in ips_str.split("<br />") if ip.strip()]
                    else:
                        return [ips_str.strip()] if ips_str.strip() else []
                else:
                    print(f"获取 {domain} 的 IP 列表失败：返回数据格式不正确")
                    return []
            else:
                print(f"请求失败，HTTP状态码: {response.status_code}，域名: {domain}")
                print(f"请求的 URL: {response.url}")
                print(f"响应内容: {response.text}")
                return []
        except httpx.ReadTimeout:
            print(f"请求超时，域名: {domain}")
            return []
            
async def ping_ip(ip: str, port: int = 80) -> tuple:
    """异步测试单个 IP 地址的延迟"""
    try:
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{ip}:{port}", timeout=2)
            latency = (time.time() - start_time) * 1000  # 转换为毫秒
            return ip, latency
    except Exception as e:
        print(f"Ping {ip} 时发生错误: {str(e)}")
        return ip, float('inf')

async def find_fastest_ip(ips: list) -> str:
    """并发测试多个 IP 地址的延迟，并找出延迟最低的 IP"""
    if not ips:
        return None
    tasks = [ping_ip(ip) for ip in ips]
    results = await asyncio.gather(*tasks)
    fastest_ip = min(results, key=lambda x: x[1])
    print("\n所有 IP 延迟情况:")
    for ip, latency in results:
        print(f"IP: {ip} - 延迟: {latency}ms")
    if fastest_ip:
        print(f"\n最快的 IP 是: {fastest_ip[0]}，延迟: {fastest_ip[1]}ms")
    return fastest_ip[0]

async def process_domain(domain: str, csrf_token: str, udp: float) -> tuple:
    """处理单个域名"""
    print(f"正在处理: {domain}")
    ipv4_ips = await get_domain_ips(domain, csrf_token, udp, "A")
    ipv6_ips = await get_domain_ips(domain, csrf_token, udp, "AAAA")
    fastest_ipv4 = await find_fastest_ip(ipv4_ips) if ipv4_ips else None
    fastest_ipv6 = await find_fastest_ip(ipv6_ips) if ipv6_ips else None
    return domain, fastest_ipv4, fastest_ipv6

async def main():
    print("开始检测相关域名的最快IP...")
    udp = random.random() * 1000 + (int(time.time() * 1000) % 1000)
    csrf_token = await get_csrf_token(udp)
    if not csrf_token:
        print("无法获取CSRF Token，程序退出")
        sys.exit(1)
    # domains_file_path = "domains.txt"
    domains_file_path  = os.path.join(os.path.dirname(__file__), "domains.txt")
    print(f"{domains_file_path}")
    if not os.path.exists(domains_file_path):
        print(f"错误：文件 {domains_file_path} 不存在！")
        sys.exit(1)
    with open(domains_file_path, "r", encoding="utf-8") as file:
        domains = [line.strip() for line in file.readlines() if line.strip()]

    # 设置最大并发数量
    max_concurrent_tasks = 5  # 你可以根据需要调整这个值
    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    async def process_domain_with_semaphore(domain):
        async with semaphore:
            return await process_domain(domain, csrf_token, udp)
    tasks = [process_domain_with_semaphore(domain) for domain in domains]
    results = await asyncio.gather(*tasks)

    ipv4_results = []
    ipv6_results = []
    for domain, fastest_ipv4, fastest_ipv6 in results:
        if fastest_ipv4:
            ipv4_results.append([fastest_ipv4, domain])
        if fastest_ipv6:
            ipv6_results.append([fastest_ipv6, domain])
    update_time = datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0).isoformat()
    # 格式化 IPv4 和 IPv6 内容
    ipv4_content = "\n".join(f"{ip:<27} {domain}" for ip, domain in ipv4_results) if ipv4_results else "# No IPv4 entries"
    ipv6_content = "\n".join(f"{ip:<50} {domain}" for ip, domain in ipv6_results) if ipv6_results else "# No IPv6 entries"
    # 使用优化后的模板生成内容
    combined_hosts_content = Hosts_TEMPLATE.format(
        update_time=update_time,
        ipv4_content=ipv4_content,
        ipv6_content=ipv6_content
    )
    # 更新 README.md 文件
    write_file(ipv4_content, ipv6_content, update_time)
    write_host_file(combined_hosts_content, "hosts")

if __name__ == "__main__":
    asyncio.run(main())
