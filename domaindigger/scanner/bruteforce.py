import uuid
from domaindigger.utils.resolver import Resolver


def brute_force(
    domain: str,
    wordlist: list[str],
    resolver: Resolver,
    on_progress=None,
) -> list[dict]:
    test = f"{uuid.uuid4().hex}.{domain}"
    wildcard_ips = resolver.resolve_a(test)
    wildcard_set = set(wildcard_ips) if wildcard_ips else set()

    fqdns = [f"{sub}.{domain}" for sub in wordlist]
    batch = resolver.resolve_batch(fqdns)

    results = []
    for i, fqdn in enumerate(fqdns):
        if on_progress:
            on_progress(i + 1, len(fqdns))
        ips = batch.get(fqdn)
        if ips:
            if wildcard_set and any(ip in wildcard_set for ip in ips):
                continue
            results.append({"subdomain": fqdn, "ips": ips, "resolved": True})

    return results
