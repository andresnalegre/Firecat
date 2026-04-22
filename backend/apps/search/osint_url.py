"""
osint_url.py — Active domain/URL intelligence
Fetches real data: IP, DNS, subdomains, headers, tech, history.
"""
import re, socket
import httpx
from typing import Any

TIMEOUT = 7
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json, text/html"}


def _r(title, link, snippet, source):
    return {"title": title, "link": link, "snippet": snippet,
            "source": source, "osint": True,
            "displayLink": re.sub(r"https?://", "", link).split("/")[0]}

def _clean(q):
    q = q.strip().lower()
    q = re.sub(r'^https?://', '', q)
    q = re.sub(r'^www\.', '', q)
    return q.split('/')[0].split('?')[0]


def _resolve_ip(domain):
    results = []
    try:
        ip = socket.gethostbyname(domain)
        ri = httpx.get(f"https://ipinfo.io/{ip}/json", timeout=TIMEOUT)
        d  = ri.json()
        results.append(_r(
            f"IP Address — {domain} → {ip}",
            f"https://ipinfo.io/{ip}",
            f"IP: {ip} · Org: {d.get('org','?')} · "
            f"City: {d.get('city','?')}, {d.get('region','?')}, {d.get('country','?')} · "
            f"Timezone: {d.get('timezone','?')} · "
            f"Hostname: {d.get('hostname','?')}",
            "ipinfo"
        ))
    except Exception:
        pass
    return results


def _dns(domain):
    results = []
    try:
        r = httpx.get(f"https://api.hackertarget.com/dnslookup/?q={domain}", timeout=TIMEOUT)
        if r.status_code == 200 and "error" not in r.text.lower():
            lines = r.text.strip().splitlines()
            by_type = {}
            for l in lines:
                parts = l.split()
                if len(parts) >= 4:
                    rtype = parts[3]
                    by_type.setdefault(rtype, []).append(" ".join(parts[4:]))
            for rtype, vals in sorted(by_type.items()):
                results.append(_r(
                    f"DNS {rtype} Records — {domain}",
                    f"https://api.hackertarget.com/dnslookup/?q={domain}",
                    f"{rtype}: " + " | ".join(vals[:5]),
                    "dns"
                ))
    except Exception:
        pass
    return results


def _subdomains(domain):
    results = []
    try:
        r = httpx.get(f"https://crt.sh/?q=%.{domain}&output=json", timeout=TIMEOUT, headers=H)
        data = r.json()
        seen, subs = set(), []
        for entry in data[:100]:
            for name in entry.get("name_value", "").split("\n"):
                name = name.strip().lower()
                if name and name not in seen and domain in name and not name.startswith("*"):
                    seen.add(name)
                    subs.append(name)
        if subs:
            results.append(_r(
                f"Subdomains — {domain} ({len(subs)} found via crt.sh)",
                f"https://crt.sh/?q=%.{domain}",
                " · ".join(subs[:25]),
                "crt.sh"
            ))
    except Exception:
        pass
    return results


def _http_headers(domain):
    results = []
    try:
        r = httpx.head(f"https://{domain}", timeout=TIMEOUT, follow_redirects=True, headers=H)
        interesting = {
            "server", "x-powered-by", "x-generator", "cf-ray", "via",
            "x-drupal-cache", "content-security-policy", "strict-transport-security",
            "x-frame-options", "x-wp-total", "x-aspnet-version"
        }
        found = {k: v for k, v in r.headers.items() if k.lower() in interesting}
        snippet = f"Status: {r.status_code} · " + " · ".join(f"{k}: {v}" for k, v in list(found.items())[:6])
        results.append(_r(
            f"HTTP Headers — {domain} [{r.status_code}]",
            f"https://{domain}",
            snippet,
            "http"
        ))
    except Exception:
        pass
    return results


def _urlscan(domain):
    results = []
    try:
        r = httpx.get(f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=5",
                      timeout=TIMEOUT, headers=H)
        for hit in r.json().get("results", [])[:3]:
            page = hit.get("page", {})
            results.append(_r(
                f"URLScan — {page.get('title', domain)}",
                hit.get("result", f"https://urlscan.io/search/#domain:{domain}"),
                f"Scanned: IP {page.get('ip','?')} · "
                f"Country: {page.get('country','?')} · "
                f"Server: {page.get('server','?')} · "
                f"ASN: {page.get('asn','?')}",
                "urlscan.io"
            ))
    except Exception:
        pass
    return results


def _wayback(domain):
    results = []
    try:
        r = httpx.get(f"https://archive.org/wayback/available?url={domain}", timeout=TIMEOUT)
        snap = r.json().get("archived_snapshots", {}).get("closest", {})
        if snap.get("available"):
            ts = snap.get("timestamp", "")
            date = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else ts
            results.append(_r(
                f"Wayback Machine — {domain} (last snapshot: {date})",
                snap.get("url", f"https://web.archive.org/web/*/{domain}"),
                f"Internet Archive snapshot of {domain} from {date}. "
                f"Status: {snap.get('status','?')}. Browse all historical versions →",
                "wayback"
            ))
    except Exception:
        pass
    return results


def _virustotal(domain):
    return [_r(
        f"VirusTotal — {domain}",
        f"https://www.virustotal.com/gui/domain/{domain}",
        f"70+ antivirus engines, passive DNS, WHOIS, and subdomains scan for {domain}.",
        "virustotal"
    )]


def _shodan(domain):
    return [_r(
        f"Shodan — {domain}",
        f"https://www.shodan.io/search?query={domain}",
        f"Shodan scan: open ports, running services, SSL info, vulnerabilities for {domain}.",
        "shodan"
    )]


def enrich_url(q: str) -> list[dict[str, Any]]:
    domain  = _clean(q)
    out     = []
    out.extend(_resolve_ip(domain))
    out.extend(_dns(domain))
    out.extend(_subdomains(domain))
    out.extend(_http_headers(domain))
    out.extend(_urlscan(domain))
    out.extend(_wayback(domain))
    out.extend(_virustotal(domain))
    out.extend(_shodan(domain))
    return out