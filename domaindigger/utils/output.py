import json
import csv
from typing import Optional
from rich.table import Table
from rich.console import Console

console = Console()


def _status_tag(code: Optional[int]) -> str:
    if code is None:
        return "[dim]---[/]"
    if 200 <= code < 300:
        return f"[green]{code}[/]"
    if 300 <= code < 400:
        return f"[yellow]{code}[/]"
    return f"[red]{code}[/]"


def print_results(results: list[dict]):
    has_http = any(r.get("http_status") is not None or r.get("https_status") is not None for r in results)
    table = Table(title="Discovered Subdomains", border_style="green")
    table.add_column("Subdomain", style="cyan")
    table.add_column("IP", style="green")
    if has_http:
        table.add_column("HTTP", justify="center")
        table.add_column("HTTPS", justify="center")
    for r in results:
        row = [
            r.get("subdomain", ""),
            ", ".join(r.get("ips", [])),
        ]
        if has_http:
            row.append(_status_tag(r.get("http_status")))
            row.append(_status_tag(r.get("https_status")))
        table.add_row(*row)
    console.print(table)


def export_json(results: list[dict], path: str):
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"[green]Results saved to {path}[/]")


def export_csv(results: list[dict], path: str):
    if not results:
        return
    has_http = any(r.get("http_status") is not None or r.get("https_status") is not None for r in results)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        headers = ["subdomain", "ip"]
        if has_http:
            headers += ["http_status", "https_status"]
        w.writerow(headers)
        for r in results:
            for ip in r.get("ips", []):
                row = [r["subdomain"], ip]
                if has_http:
                    row += [r.get("http_status", ""), r.get("https_status", "")]
                w.writerow(row)
    console.print(f"[green]Results saved to {path}[/]")


def export_txt(results: list[dict], path: str):
    with open(path, "w") as f:
        for r in results:
            ips = ", ".join(r.get("ips", []))
            http = r.get("http_status") or ""
            https = r.get("https_status") or ""
            line = f"{r['subdomain']} [{ips}]"
            if http or https:
                line += f" HTTP:{http} HTTPS:{https}"
            f.write(line + "\n")
    console.print(f"[green]Results saved to {path}[/]")


def export_results(results: list[dict], path: Optional[str] = None, fmt: Optional[str] = None):
    if path is None:
        print_results(results)
        return

    if fmt is None:
        ext = path.rsplit(".", 1)[-1].lower()
        fmt = ext if ext in ("json", "csv", "txt") else "txt"

    if fmt == "json":
        export_json(results, path)
    elif fmt == "csv":
        export_csv(results, path)
    else:
        export_txt(results, path)
