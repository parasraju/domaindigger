import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
_SESSION = requests.Session()
_SESSION.headers.update(_HEADERS)


def _get(url: str, timeout: int = 20, retries: int = 1):
    for attempt in range(retries + 1):
        try:
            r = _SESSION.get(url, timeout=timeout)
            if r.status_code == 429:
                if attempt < retries:
                    time.sleep(1)
                    continue
                return None
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(1)
                continue
            return None
        except Exception:
            return None
    return None


def _get_json(url: str, timeout: int = 20):
    t = _get(url, timeout)
    if t:
        try:
            return json.loads(t)
        except json.JSONDecodeError:
            return None
    return None


def _crt_fetch(url: str) -> list | None:
    data = _get_json(url, timeout=20)
    if data and isinstance(data, list):
        return data
    return None


def crtsh(domain: str) -> set[str]:
    urls = [
        f"https://crt.sh/?identity=%25.{domain}&output=json",
        f"http://crt.sh/?q=%25.{domain}&output=json",
    ]
    data = None
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut = {pool.submit(_crt_fetch, u): u for u in urls}
        for f in as_completed(fut):
            r = f.result()
            if r:
                data = r
                break
    subs = set()
    if data:
        for e in data:
            for name in str(e.get("name_value", "")).split("\n"):
                name = name.strip().lower()
                if name.startswith("*."):
                    name = name[2:]
                if name.endswith("." + domain) and name != domain:
                    subs.add(name)
    return subs


def urlscan(domain: str) -> set[str]:
    subs = set()
    data = _get_json(f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=100")
    if data and "results" in data:
        for r in data["results"]:
            dom = r.get("page", {}).get("domain", "")
            if dom.endswith("." + domain):
                subs.add(dom.lower())
    return subs


def hackertarget(domain: str) -> set[str]:
    subs = set()
    text = _get(f"https://api.hackertarget.com/hostsearch/?q={domain}")
    if text and "API count exceeded" not in text:
        for line in text.strip().split("\n"):
            parts = line.split(",")
            if len(parts) >= 2:
                sub = parts[0].strip().lower()
                if sub.endswith("." + domain):
                    subs.add(sub)
    return subs


def rapiddns(domain: str) -> set[str]:
    subs = set()
    html = _get(f"https://rapiddns.io/subdomain/{domain}")
    if html:
        for m in re.finditer(r">([a-zA-Z0-9._-]+\." + re.escape(domain) + r")<", html):
            sub = m.group(1).lower()
            if sub.endswith("." + domain) and sub != domain:
                subs.add(sub)
    return subs


_SOURCES = [
    ("crt.sh", crtsh),
    ("RapidDNS", rapiddns),
    ("URLScan", urlscan),
    ("HackerTarget", hackertarget),
]


def gather_passive(domain: str) -> dict[str, set[str]]:
    results: dict[str, set[str]] = {}
    with ThreadPoolExecutor(max_workers=len(_SOURCES)) as pool:
        fut = {pool.submit(func, domain): name for name, func in _SOURCES}
        for f in as_completed(fut):
            name = fut[f]
            try:
                results[name] = f.result()
            except Exception:
                results[name] = set()
    return results
