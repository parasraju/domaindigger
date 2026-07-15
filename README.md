<div align="center">
  <pre>
██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗
██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║
██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║
██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║
██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
██████╗ ██╗ ██████╗  ██████╗ ███████╗██████╗
██╔══██╗██║██╔════╝ ██╔════╝ ██╔════╝██╔══██╗
██║  ██║██║██║  ███╗██║  ███╗█████╗  ██████╔╝
██║  ██║██║██║   ██║██║   ██║██╔══╝  ██╔══██╗
██████╔╝██║╚██████╔╝╚██████╔╝███████╗██║  ██║
╚═════╝ ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
  </pre>
  <p><strong>made by Paras</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat&logo=python">
    <img src="https://img.shields.io/badge/license-MIT-brightgreen">
  </p>
</div>

---

## 📦 Install

```bash
pip install rich requests dnspython pyfiglet

# clone and install
git clone https://github.com/paras/domaindigger.git
cd domaindigger
pip install .
```

## 🚀 Usage

```bash
domaindigger hackerone.com
```

### Flags

| Flag | Description |
|---|---|
| `-p` | 🌐 Probe HTTP/HTTPS and show status codes |
| `-d` | 🔄 Enable DNS brute-force |
| `-w <file>` | 📂 Custom wordlist (implies `-d`) |
| `-t <n>` | ⚡ Threads (default: 20) |
| `-o <file>` | 💾 Save results (.json / .csv / .txt) |
| `-f <fmt>` | 📄 Force format: json, csv, txt |

### Examples

```bash
# quick passive scan
domaindigger example.com

# passive + brute-force
domaindigger example.com -d

# passive scan + HTTP probe
domaindigger example.com -p

# passive + brute-force
domaindigger example.com -d

# custom wordlist, 50 threads, json output
domaindigger example.com -w big.txt -t 50 -o results.json
```

## 🔍 Sources

| Source | Type | Key Required |
|---|---|---|
| [crt.sh](https://crt.sh) | Certificate Transparency | ❌ |
| [URLScan.io](https://urlscan.io) | Web Crawler | ❌ |
| [HackerTarget](https://hackertarget.com) | DNS Enumeration | ❌ |

## ⚙️ How It Works

```
┌──────────────┐
│   Input      │  domain + flags
└──────┬───────┘
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   crt.sh     │     │   URLScan    │     │ HackerTarget │
│  (parallel)  │────▶│  (parallel)  │────▶│  (parallel)  │
└──────────────┘     └──────────────┘     └──────────────┘
       │                     │                    │
       └─────────────┬───────┴────────────┬───────┘
                     ▼                    ▼
            ┌────────────────┐   ┌────────────────┐
            │  Dedup + DNS   │   │  Brute-force   │
            │  Resolution    │   │  (optional -d) │
            └───────┬────────┘   └───────┬────────┘
                    │                    │
                    └────────┬───────────┘
                             ▼
                    ┌────────────────┐
                    │  Rich Output   │
                    │  Table / JSON  │
                    │  / CSV / TXT   │
                    └────────────────┘
```

## 📄 License

MIT
