"""
osint_email.py — Active email intelligence
Fetches real data: breach status, social accounts, domain MX, reputation.
All results have osint=True to bypass the relevance filter.
"""
import re, socket, hashlib
import httpx
from typing import Any

TIMEOUT = 7
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def _r(title, link, snippet, source):
    return {"title": title, "link": link, "snippet": snippet,
            "source": source, "osint": True,
            "displayLink": re.sub(r"https?://", "", link).split("/")[0]}

def _domain(email):
    p = email.split("@")
    return p[1] if len(p) == 2 else ""


def _emailrep(email):
    results = []
    try:
        r = httpx.get(f"https://emailrep.io/{email}", timeout=TIMEOUT,
                      headers={**H, "Key": "emailrep-free"})
        d = r.json()
        rep      = d.get("reputation", "unknown")
        details  = d.get("details", {})
        profiles = details.get("profiles", [])
        refs     = d.get("references", 0)
        sus      = d.get("suspicious", False)
        snippet  = (
            f"Reputation: {rep.upper()} · "
            f"Suspicious: {'⚠ YES' if sus else 'no'} · "
            f"Deliverable: {details.get('deliverable','?')} · "
            f"References: {refs} · "
            f"First seen: {details.get('first_seen','?')} · "
            f"Last seen: {details.get('last_seen','?')}"
        )
        if profiles:
            snippet += f" · Profiles: {', '.join(profiles)}"
        results.append(_r(f"Email Reputation — {email} [{rep.upper()}]",
                          f"https://emailrep.io/{email}", snippet, "emailrep.io"))
        for p in profiles:
            results.append(_r(f"Account on {p.title()} — {email}",
                              f"https://www.{p}.com",
                              f"EmailRep confirmed {email} is linked to a {p.title()} account.",
                              "emailrep.io"))
    except Exception:
        pass
    return results


def _mx_records(email):
    results = []
    domain = _domain(email)
    if not domain:
        return results
    try:
        r = httpx.get(f"https://api.hackertarget.com/dnslookup/?q={domain}", timeout=TIMEOUT)
        if r.status_code == 200 and "error" not in r.text.lower():
            lines = r.text.strip().splitlines()
            mx = [l for l in lines if " MX " in l]
            a  = [l for l in lines if " A "  in l]
            snippet = ""
            if mx: snippet += "MX: " + " | ".join(mx[:3])
            if a:  snippet += (" · " if snippet else "") + "A: " + " | ".join(a[:2])
            if snippet:
                results.append(_r(f"DNS / Mail Server — {domain}",
                    f"https://mxtoolbox.com/SuperTool.aspx?action=mx:{domain}",
                    snippet, "dns"))
        ip = socket.gethostbyname(domain)
        ri = httpx.get(f"https://ipinfo.io/{ip}/json", timeout=TIMEOUT)
        d  = ri.json()
        results.append(_r(f"Mail Server IP — {ip} ({d.get('org','?')})",
            f"https://ipinfo.io/{ip}",
            f"Domain {domain} resolves to {ip} · Org: {d.get('org','?')} · "
            f"City: {d.get('city','?')}, {d.get('country','?')}", "ipinfo"))
    except Exception:
        pass
    return results


def _paste_search(email):
    results = []
    try:
        r = httpx.get(f"https://psbdmp.ws/api/v3/search/{email}", timeout=TIMEOUT, headers=H)
        dumps = r.json().get("data", [])
        for d in dumps[:5]:
            results.append(_r(f"Pastebin Dump — {d.get('id','')}",
                f"https://pastebin.com/{d.get('id','')}",
                f"Email {email} found in paste from {d.get('time','?')}. Tags: {d.get('tags','?')}",
                "pastebin"))
        if not dumps:
            results.append(_r(f"Pastebin — No indexed dumps for {email}",
                f"https://pastebin.com/search?q={email}",
                f"No psbdmp entries found. Manual Pastebin search recommended.", "pastebin"))
    except Exception:
        results.append(_r(f"Pastebin — {email}", f"https://pastebin.com/search?q={email}",
                          f"Search Pastebin for pastes containing {email}.", "pastebin"))
    return results


def _hunter(email):
    domain = _domain(email)
    if not domain:
        return []
    try:
        r = httpx.get(f"https://api.hunter.io/v2/email-verifier?email={email}&api_key=free",
                      timeout=TIMEOUT, headers=H)
        d = r.json().get("data", {})
        return [_r(f"Hunter.io Verify — {email} [{d.get('status','?')}]",
                   f"https://hunter.io/verify/{email}",
                   f"Status: {d.get('status','?')} · Score: {d.get('score','?')}/100 · "
                   f"MX: {d.get('mx_records','?')} · SMTP: {d.get('smtp_server','?')}",
                   "hunter.io")]
    except Exception:
        return [_r(f"Hunter.io — {email}", f"https://hunter.io/verify/{email}",
                   f"Verify deliverability and organisation for {email}.", "hunter.io")]


def _gravatar(email):
    h = hashlib.md5(email.encode()).hexdigest()
    return [_r(f"Gravatar — {email}",
               f"https://en.gravatar.com/{h}",
               f"Gravatar profile lookup for {email}. If registered reveals avatar, name and bio.",
               "gravatar")]


def _breach_links(email):
    return [
        _r(f"HaveIBeenPwned — {email}", f"https://haveibeenpwned.com/account/{email}",
           f"Check if {email} appeared in 700+ known data breaches.", "hibp"),
        _r(f"DeHashed — {email}", f"https://dehashed.com/search?query={email}",
           f"Search {email} across leaked credential databases: passwords, IPs, usernames.", "dehashed"),
        _r(f"LeakCheck — {email}", f"https://leakcheck.io/?query={email}",
           f"LeakCheck: source, date and exposed fields for {email}.", "leakcheck"),
        _r(f"IntelX — {email}", f"https://intelx.io/?s={email}",
           f"Search {email} across dark web, pastes and leaked documents.", "intelx"),
        _r(f"Epieos — {email}", f"https://epieos.com/?q={email}&type=email",
           f"Find Google account, profile photo and Calendar ID tied to {email}.", "epieos"),
    ]


def enrich_email(q: str) -> list[dict[str, Any]]:
    email = q.strip().lower()
    out   = []
    out.extend(_emailrep(email))
    out.extend(_mx_records(email))
    out.extend(_hunter(email))
    out.extend(_paste_search(email))
    out.extend(_breach_links(email))
    out.extend(_gravatar(email))
    return out