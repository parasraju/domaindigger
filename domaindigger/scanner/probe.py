import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def _check(subdomain: str, timeout: int = 5) -> dict:
    result = {"subdomain": subdomain, "http_status": None, "https_status": None, "alive": False}
    for proto in ("http", "https"):
        try:
            r = requests.get(f"{proto}://{subdomain}", timeout=timeout, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            result[f"{proto}_status"] = r.status_code
            result["alive"] = True
        except Exception:
            pass
    return result


def probe_batch(subdomains: list[str], threads: int = 20, timeout: int = 5) -> list[dict]:
    results = []
    with ThreadPoolExecutor(max_workers=threads) as pool:
        fut = {pool.submit(_check, s, timeout): s for s in subdomains}
        for f in as_completed(fut):
            results.append(f.result())
    results.sort(key=lambda x: x["subdomain"])
    return results
