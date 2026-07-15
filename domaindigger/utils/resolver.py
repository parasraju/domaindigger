import dns.resolver
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

_RESOLVERS = [
    "1.1.1.1",
    "1.0.0.1",
    "8.8.8.8",
    "8.8.4.4",
]


class Resolver:
    def __init__(self, threads: int = 20, timeout: int = 5):
        self.threads = threads
        self._pool = []
        for ip in _RESOLVERS:
            r = dns.resolver.Resolver()
            r.nameservers = [ip]
            r.timeout = timeout
            r.lifetime = timeout
            self._pool.append(r)

    def resolve_a(self, hostname: str) -> Optional[list[str]]:
        resolvers = random.sample(self._pool, min(2, len(self._pool)))
        for r in resolvers:
            try:
                answers = r.resolve(hostname, "A", raise_on_no_answer=False)
                return [str(x) for x in answers]
            except Exception:
                continue
        return None

    def resolve_batch(self, hostnames: list[str]) -> dict[str, Optional[list[str]]]:
        results = {}
        with ThreadPoolExecutor(max_workers=self.threads) as pool:
            fut = {pool.submit(self.resolve_a, h): h for h in hostnames}
            for f in as_completed(fut):
                h = fut[f]
                try:
                    results[h] = f.result()
                except Exception:
                    results[h] = None
        return results
