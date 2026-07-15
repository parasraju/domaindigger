from domaindigger.utils.resolver import Resolver


def collect_dns(hostname: str, resolver: Resolver) -> dict:
    ips = resolver.resolve_a(hostname)
    return {
        "subdomain": hostname,
        "ips": ips or [],
        "resolved": ips is not None,
    }
