import json
import csv
from typing import Optional
from rich.table import Table
from rich.console import Console

console = Console()


def print_results(results: list[dict]):
    table = Table(title="Discovered Subdomains", border_style="green")
    table.add_column("Subdomain", style="cyan")
    table.add_column("IP", style="green")
    for r in results:
        table.add_row(
            r.get("subdomain", ""),
            ", ".join(r.get("ips", [])),
        )
    console.print(table)


def export_json(results: list[dict], path: str):
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"[green]Results saved to {path}[/]")


def export_csv(results: list[dict], path: str):
    if not results:
        return
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["subdomain", "ip"])
        for r in results:
            for ip in r.get("ips", []):
                w.writerow([r["subdomain"], ip])
    console.print(f"[green]Results saved to {path}[/]")


def export_txt(results: list[dict], path: str):
    with open(path, "w") as f:
        for r in results:
            ips = ", ".join(r.get("ips", []))
            f.write(f"{r['subdomain']} [{ips}]\n")
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
