import requests
from time import sleep
import random
import time
import os
import sys
from datetime import datetime, timezone, timedelta
from retry import retry
import socket
import asyncio

Tmdb_Host_TEMPLATE = """# Tmdb Hosts Start
{content}
# Update time: {update_time}
# IPv4 Update url: https://raw.githubusercontent.com/938134/CheckTMDB/refs/heads/main/Tmdb_host_ipv4
# IPv6 Update url: https://raw.githubusercontent.com/938134/CheckTMDB/refs/heads/main/Tmdb_host_ipv6
# Star me: https://github.com/938134/CheckTMDB
# Tmdb Hosts End\n"""

def write_file(ipv4_hosts_content: str, ipv6_hosts_content: str, update_time: str) -> bool:
    output_doc_file_path = os.path.join(os.path.dirname(__file__), "README.md")
    template_path = os.path.join(os.path.dirname(__file__), "README_template.md")
    if os.path.exists(output_doc_file_path):
        with open(output_doc_file_path, "r", encoding='utf-8') as old_readme_md:
            old_readme_md_content = old_readme_md.read()            
            if old_readme_md_content:
                old_ipv4_block = old_readme_md_content.split("```bash")[1].split("```")[0].strip()
                old_ipv4_hosts = old_ipv4_block.split("# Update time:")[0].strip()
                old_ipv6_block = old_readme_md_content.split("```bash")[2].split("```")[0].strip()
                old_ipv6_hosts = old_ipv6_block.split("# Update time:")[0].strip()
                if ipv4_hosts_content != "":
                    new_ipv4_hosts = ipv4_hosts_content.split("# Update time:")[0].strip()
                    if old_ipv4_hosts == new_ipv4_hosts:
                        print("ipv4 host not change")
                        w_ipv4_block = old_ipv4_block
                    else:
                        w_ipv4_block = ipv4_hosts_content
                        write_host_file(ipv4_hosts_content, 'ipv4')
                else:
                    print("ipv4_hosts_content is null")
                    w_ipv4_block = old_ipv4_block
                if ipv6_hosts_content != "":
                    new_ipv6_hosts = ipv6_hosts_content.split("# Update time:")[0].strip()
                    if old_ipv6_hosts == new_ipv6_hosts:
                        print("ipv6 host not change")
                        w_ipv6_block = old_ipv6_block
                    else:
                        w_ipv6_block = ipv6_hosts_content
                        write_host_file(ipv6_hosts_content, 'ipv6')
                else:
                    print("ipv6_hosts_content is null")
                    w_ipv6_block = old_ipv6_block
                
                with open(template_path, "r", encoding='utf-8') as temp_fb:
                    template_str = temp_fb.read()
                    hosts_content = template_str.format(ipv4_hosts_str=w_ipv4_block, ipv6_hosts_str=w_ipv6_block, update_time=update_time)

                    with open(output_doc_file_path, "w", encoding='utf-8') as output_fb:
                        output_fb.write(hosts_content)
                return True
        return False
               
def write_host_file(hosts_content: str, filename: str) -> None:
    output_file_path = os.path.join(os.path.dirname(__file__), "Tmdb_host_" + filename)
    if len(sys.argv) >= 2 and sys.argv[1].upper() == '-G':
        print("\n~追加Github ip~")
        hosts_content = hosts_content + "\n" + (get_github_hosts() or "")
    with open(output_file_path, "w", encoding='utf-8') as output_fb:
        output_fb.write(hosts_content)
        print("\n~最新TMDB" + filename + "地址已更新~")

def get_github_hosts() -> None:
    github_hosts_urls = [
        "https://hosts.gitcdn.top/hosts.txt",
        "https://raw.githubusercontent.com/521xueweihan/GitHub520/refs/heads/main/hosts",
        "https://gitlab.com/ineo6/hosts/-/raw/master/next-hosts",
        "https://raw.githubusercontent.com/ittuann/GitHub-IP-hosts/refs/heads/main/hosts_single"
    ]
    all_failed = True
    for url in github_hosts_urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                github_hosts = response.text
                all_failed = False
                break
            else:
                print(f"\n从 {url} 获取GitHub hosts失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"\n从 {url} 获取GitHub hosts时发生错误: {str(e)}")
    if all_failed:
        print("\n获取GitHub hosts失败: 所有Url项目失败！")
        return
    else:
        return github_hosts

def is_ci_environment():
    ci_environment_vars = {
        'GITHUB_ACTIONS': 'true',
        'TRAVIS': 'true',
        'CIRCLECI': 'true'
    }
    for env_var, expected_value in ci_environment_vars.items():
        env_value = os.getenv(env_var)
        if env_value is not None and str(env_value).lower() == expected_value.lower():
            return True
    return False
    
# """异步测试单个 IP 地址的延迟"""
async def ping_ip(ip, port=80):
    try:
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{ip}:{port}", timeout=2) as response:
                latency = (time.time() - start_time) * 1000  # 转换为毫秒
                return ip, latency
    except Exception as e:
        print(f"Ping {ip} 时发生错误: {str(e)}")
        return ip, float('inf')
        
# """并发测试多个 IP 地址的延迟，并找出延迟最低的 IP"""
async def find_fastest_ip(ips):
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

def get_csrf_token(udp: float) -> str:
    """获取 CSRF Token"""
    url = "https://dnschecker.org/ajax_files/gen_csrf.php"
    headers = {
        "referer": "https://dnschecker.org/country/cn/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    }
    params = {"udp": udp}
    response_data = make_dnschecker_request(url, headers, params)
    csrf_token = response_data.get("csrf")
    if csrf_token:
        print(f"获取到的 CSRF Token: {csrf_token}")
        return csrf_token
    else:
        print("无法获取 CSRF Token")
        return None

def get_domain_ips(domain: str, csrf_token: str, udp: float, record_type: str) -> list:
    """获取域名的 IPv4 或 IPv6 地址"""
    url = f"https://dnschecker.org/ajax_files/api/363/{record_type}"
    headers = {
        "csrftoken": csrf_token,
        "referer": "https://dnschecker.org/country/cn/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    }
    params = {
        "dns_key": "country",
        "dns_value": "cn",
        "v": 0.36,
        "cd_flag": 1,
        "upd": udp,
        "domain": domain
    }

    response_data = make_dnschecker_request(url, headers, params)
    if "result" in response_data and "ips" in response_data["result"]:
        ips_str = response_data["result"]["ips"]
        if "<br />" in ips_str:
            return [ip.strip() for ip in ips_str.split("<br />") if ip.strip()]
        else:
            return [ips_str.strip()] if ips_str.strip() else []
    else:
        print(f"获取 {domain} 的 IP 列表失败：返回数据格式不正确")
        return []
    
def make_dnschecker_request(url: str, headers: dict, params: dict = None) -> dict:
    """通用函数：发送请求到 DNSChecker API"""
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，HTTP状态码: {response.status_code}")
            return {}
    except Exception as e:
        print(f"请求时发生错误: {str(e)}")
        return {}
        
async def main():
    print("开始检测TMDB相关域名的最快IP...")
    udp = random.random() * 1000 + (int(time.time() * 1000) % 1000)
    # 获取CSRF Token
    csrf_token = get_csrf_token(udp)
    if not csrf_token:
        print("无法获取CSRF Token，程序退出")
        sys.exit(1) 
    ipv4_ips, ipv6_ips, ipv4_results, ipv6_results = [], [], [], []
    for domain in DOMAINS:
        print(f"\n正在处理域名: {domain}")       
        ipv4_ips = get_domain_ips(domain, csrf_token, udp, "A")
        ipv6_ips = get_domain_ips(domain, csrf_token, udp, "AAAA")

        if not ipv4_ips and not ipv6_ips:
            print(f"无法获取 {domain} 的IP列表，跳过该域名")
            continue
        
        # 处理 IPv4 地址
        if ipv4_ips:
            fastest_ipv4 = find_fastest_ip(ipv4_ips)
            if fastest_ipv4:
                ipv4_results.append([fastest_ipv4, domain])
                print(f"域名 {domain} 的最快IPv4是: {fastest_ipv4}")
            else:
                ipv4_results.append([ipv4_ips[0], domain])
        
        # 处理 IPv6 地址
        if ipv6_ips:
            fastest_ipv6 = find_fastest_ip(ipv6_ips)
            if fastest_ipv6:
                ipv6_results.append([fastest_ipv6, domain])
                print(f"域名 {domain} 的最快IPv6是: {fastest_ipv6}")
            else:
                # 兜底：可能存在无法正确获取 fastest_ipv6 的情况，则将第一个IP赋值
                ipv6_results.append([ipv6_ips[0], domain])
        
        sleep(1)  # 避免请求过于频繁
    
    # 保存结果到文件
    if not ipv4_results and not ipv6_results:
        print(f"程序出错：未获取任何domain及对应IP，请检查接口~")
        sys.exit(1)

    # 生成更新时间
    update_time = datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0).isoformat()
    ipv4_hosts_content = Tmdb_Host_TEMPLATE.format(content="\n".join(f"{ip:<27} {domain}" for ip, domain in ipv4_results), update_time=update_time) if ipv4_results else ""
    ipv6_hosts_content = Tmdb_Host_TEMPLATE.format(content="\n".join(f"{ip:<50} {domain}" for ip, domain in ipv6_results), update_time=update_time) if ipv6_results else ""
    write_file(ipv4_hosts_content, ipv6_hosts_content, update_time)

# 读取 domains.txt 文件中的域名
def load_domains_from_file(file_path: str) -> list:
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在！")
        return []
    with open(file_path, "r", encoding="utf-8") as file:
        domains = [line.strip() for line in file.readlines() if line.strip()]
    return domains

if __name__ == "__main__":
    # 加载域名列表
    domains_file_path = "domains.txt"
    DOMAINS = load_domains_from_file(domains_file_path)
    if not DOMAINS:
        print("未加载到任何域名，程序退出。")
        sys.exit(1)
    asyncio.run(main())
