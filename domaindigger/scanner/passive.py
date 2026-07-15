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
                return None, "rate limited (429)"
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text, None
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(1)
                continue
            return None, "timed out"
        except requests.exceptions.HTTPError as e:
            return None, f"HTTP {e.response.status_code}"
        except Exception:
            return None, "connection failed"
    return None, "max retries exceeded"


def _get_json(url: str, timeout: int = 20):
    t, err = _get(url, timeout)
    if err:
        return None, err
    if t:
        try:
            return json.loads(t), None
        except json.JSONDecodeError:
            return None, "bad JSON response"
    return None, "empty response"


def _crt_fetch(url: str) -> tuple[list | None, str | None]:
    data, err = _get_json(url, timeout=20)
    if err:
        return None, err
    if isinstance(data, list):
        return data, None
    return None, "unexpected response format"


def crtsh(domain: str) -> tuple[set[str], str | None]:
    urls = [
        f"https://crt.sh/?identity=%25.{domain}&output=json",
        f"http://crt.sh/?q=%25.{domain}&output=json",
    ]
    errors = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut = {pool.submit(_crt_fetch, u): u for u in urls}
        for f in as_completed(fut):
            data, err = f.result()
            if data:
                subs = set()
                for e in data:
                    for name in str(e.get("name_value", "")).split("\n"):
                        name = name.strip().lower()
                        if name.startswith("*."):
                            name = name[2:]
                        if name.endswith("." + domain) and name != domain:
                            subs.add(name)
                return subs, None
            errors.append(err or "unknown")
    return set(), "; ".join(errors)


def urlscan(domain: str) -> tuple[set[str], str | None]:
    data, err = _get_json(f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=100")
    if err:
        return set(), err
    subs = set()
    if "results" in data:
        for r in data["results"]:
            dom = r.get("page", {}).get("domain", "")
            if dom.endswith("." + domain):
                subs.add(dom.lower())
    return subs, None


def hackertarget(domain: str) -> tuple[set[str], str | None]:
    text, err = _get(f"https://api.hackertarget.com/hostsearch/?q={domain}")
    if err:
        return set(), err
    if "API count exceeded" in text:
        return set(), "rate limited"
    subs = set()
    for line in text.strip().split("\n"):
        parts = line.split(",")
        if len(parts) >= 2:
            sub = parts[0].strip().lower()
            if sub.endswith("." + domain):
                subs.add(sub)
    return subs, None


def rapiddns(domain: str) -> tuple[set[str], str | None]:
    html, err = _get(f"https://rapiddns.io/subdomain/{domain}")
    if err:
        return set(), err
    subs = set()
    for m in re.finditer(r">([a-zA-Z0-9._-]+\." + re.escape(domain) + r")<", html):
        sub = m.group(1).lower()
        if sub.endswith("." + domain) and sub != domain:
            subs.add(sub)
    return subs, "ok" if not subs else None


_SOURCES = [
    ("crt.sh", crtsh),
    ("RapidDNS", rapiddns),
    ("URLScan", urlscan),
    ("HackerTarget", hackertarget),
]


def gather_passive(domain: str) -> dict[str, tuple[set[str], str | None]]:
    results: dict[str, tuple[set[str], str | None]] = {}
    with ThreadPoolExecutor(max_workers=len(_SOURCES)) as pool:
        fut = {pool.submit(func, domain): name for name, func in _SOURCES}
        for f in as_completed(fut):
            name = fut[f]
            try:
                results[name] = f.result()
            except Exception as e:
                results[name] = (set(), str(e))
    return results
