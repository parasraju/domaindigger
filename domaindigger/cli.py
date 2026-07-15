import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from domaindigger.banner import show_banner
from domaindigger.utils.resolver import Resolver
from domaindigger.utils.wordlist import load_wordlist
from domaindigger.utils.output import export_results
from domaindigger.scanner.bruteforce import brute_force
from domaindigger.scanner.passive import gather_passive
from domaindigger.scanner.probe import probe_batch

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn

console = Console(color_system="truecolor")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="domaindigger",
        description="Domain reconnaissance made simple",
    )
    p.add_argument("domain", help="Target domain (e.g. example.com)")
    p.add_argument("-d", "--bruteforce", action="store_true", help="Enable DNS brute-force")
    p.add_argument("-w", "--wordlist", help="Custom wordlist for brute-force")
    p.add_argument("-p", "--http-probe", action="store_true", help="Probe HTTP/HTTPS endpoints")
    p.add_argument("-t", "--threads", type=int, default=20, help="Threads (default: 20)")
    p.add_argument("-o", "--output", help="Output file path")
    p.add_argument("-f", "--format", choices=["json", "csv", "txt"], help="Output format")
    p.add_argument("--no-banner", action="store_true", help="Skip banner")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if not args.no_banner:
        show_banner()

    domain = args.domain.lower().strip()
    resolver = Resolver(threads=args.threads, timeout=5)
    all_subs: set[str] = set()
    sources: list[str] = []

    console.print("\n[bold cyan][*] Passive reconnaissance...[/]")
    passive = gather_passive(domain)
    for src, (subs, err) in passive.items():
        sources.append(src)
        before = len(all_subs)
        all_subs.update(subs)
        count = len(all_subs) - before
        if count:
            icon, style = "[green]+[/]", "cyan"
        elif err:
            icon, style = f"[dim]-[/]", "dim"
        else:
            icon, style = "[dim]-[/]", "dim"
        label = f"[{style}]{src}[/]"
        if err:
            label += f" [dim]({err})[/]"
        console.print(f"  {icon} {label}: [cyan]{count}[/]")
    console.print(f"  Total: [cyan]{len(all_subs)}[/]\n")

    if args.bruteforce or args.wordlist:
        wl = load_wordlist(args.wordlist) if args.wordlist else [
            "www", "mail", "ftp", "admin", "api", "dev", "test", "blog",
            "webmail", "smtp", "vpn", "git", "wiki", "docs", "cdn", "app",
            "portal", "login", "auth", "beta", "demo", "shop", "status",
            "backup", "db", "cache", "monitor", "logs", "jenkins", "search",
            "remote", "download", "uploads", "static", "assets", "images",
            "partner", "sandbox", "qa", "corp", "ns1", "ns2", "mx",
            "owa", "autodiscover", "sip", "helpdesk",
        ]
        console.print(f"[bold cyan][*] Brute-forcing {len(wl)} subdomains...[/]")
        found = []
        with Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as p:
            t = p.add_task("Resolving...", total=len(wl))
            def cb(c, _): p.update(t, completed=c)
            found = brute_force(domain, wl, resolver, on_progress=cb)
        console.print(f"  [green]+[/] Brute-force: [cyan]{len(found)}[/] resolved\n")
        for f in found:
            all_subs.add(f["subdomain"])
        sources.append("Brute-force")

    if not all_subs:
        console.print("[yellow]No subdomains found.[/]")
        return 0

    console.print(f"[bold cyan][*] Resolving {len(all_subs)} subdomains...[/]")
    subs_sorted = sorted(all_subs)
    results = []
    with Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as p:
        t = p.add_task("Resolving...", total=len(subs_sorted))
        with ThreadPoolExecutor(max_workers=args.threads) as pool:
            fut = {pool.submit(resolver.resolve_a, sub): sub for sub in subs_sorted}
            for f in as_completed(fut):
                sub = fut[f]
                ips = f.result()
                if ips:
                    results.append({"subdomain": sub, "ips": ips, "resolved": True})
                p.update(t, advance=1)

    if args.http_probe and results:
        console.print(f"[bold cyan][*] HTTP probing {len(results)} subdomains...[/]")
        subdomains = [r["subdomain"] for r in results]
        probe_results = probe_batch(subdomains, threads=args.threads, timeout=5)
        probe_map = {p["subdomain"]: p for p in probe_results}
        for r in results:
            p = probe_map.get(r["subdomain"], {})
            r["http_status"] = p.get("http_status")
            r["https_status"] = p.get("https_status")

    console.print()
    export_results(results, args.output, args.format)
    console.print(f"\n[bold green]Done.[/] [cyan]{len(results)}[/] subdomains found")
    if sources:
        console.print(f"Sources: {', '.join(sources)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
