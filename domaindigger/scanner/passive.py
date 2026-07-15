import json
import time
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
        for enc in ("utf-8", "latin-1", None):
            try:
                return json.loads(t)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
    return None


def crtsh(domain: str) -> set[str]:
    subs = set()
    data = _get_json(f"http://crt.sh/?q=%25.{domain}&output=json", timeout=30)
    if data and isinstance(data, list):
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


_SOURCES = [
    ("crt.sh", crtsh),
    ("URLScan", urlscan),
    ("HackerTarget", hackertarget),
]


def gather_passive(domain: str) -> dict[str, set[str]]:
    results = {}
    for name, func in _SOURCES:
        try:
            subs = func(domain)
            if subs:
                results[name] = subs
        except Exception:
            pass
    return results
