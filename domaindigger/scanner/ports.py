import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

TOP_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143,
    443, 445, 993, 995, 1433, 1723, 3306, 3389, 5900,
    6379, 8000, 8080, 8443, 9090, 27017,
]


def _scan(ip: str, port: int, timeout: int = 3) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((ip, port)) == 0
    except Exception:
        return False
    finally:
        s.close()


def scan_batch(
    ips: list[str],
    ports: Optional[list[int]] = None,
    threads: int = 20,
    timeout: int = 3,
    on_progress=None,
) -> dict[str, list[int]]:
    ports = ports or TOP_PORTS
    tasks = [(ip, port) for ip in ips for port in ports]
    open_ports: dict[str, list[int]] = {ip: [] for ip in ips}
    done = [0]

    def track(fut):
        done[0] += 1
        if on_progress:
            on_progress(done[0], len(tasks))

    with ThreadPoolExecutor(max_workers=threads) as pool:
        fut = {pool.submit(_scan, ip, port, timeout): (ip, port) for ip, port in tasks}
        for f in as_completed(fut):
            ip, port = fut[f]
            try:
                if f.result():
                    open_ports[ip].append(port)
            except Exception:
                pass
            track(f)

    return {ip: sorted(ports) for ip, ports in open_ports.items() if ports}