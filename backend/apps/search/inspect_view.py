from __future__ import annotations

import re
import ssl
import random
from urllib.parse import urlparse, urljoin
from typing import Any

import httpx
from bs4 import BeautifulSoup, Comment
from django.http import JsonResponse
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Regex patterns
EMAIL_RE    = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
PHONE_RE    = re.compile(r'(?:\+\d{1,3}[\s\-.]?)?\(?\d{2,4}\)?[\s\-.]?\d{3,5}[\s\-.]?\d{3,5}(?:[\s\-.]?\d{1,5})?')
IPV4_RE     = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
SOCIAL_RE   = re.compile(
    r'https?://(?:www\.)?('
    r'twitter\.com/[^\s"\'>]+|'
    r'x\.com/[^\s"\'>]+|'
    r'linkedin\.com/in/[^\s"\'>]+|'
    r'instagram\.com/[^\s"\'>]+|'
    r'facebook\.com/[^\s"\'>]+|'
    r'github\.com/[^\s"\'>]+|'
    r'youtube\.com/(?:channel|c|@)[^\s"\'>]+|'
    r'tiktok\.com/@[^\s"\'>]+|'
    r'reddit\.com/u(?:ser)?/[^\s"\'>]+|'
    r'pinterest\.com/[^\s"\'>]+|'
    r'discord\.gg/[^\s"\'>]+|'
    r't\.me/[^\s"\'>]+'
    r')', re.IGNORECASE
)
CRYPTO_RE   = re.compile(r'\b(1[13-9A-HJ-NP-Za-km-z]{25,34}|3[A-HJ-NP-Za-km-z]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{39,59}|0x[a-fA-F0-9]{40})\b')
API_KEY_RE  = re.compile(r'(?:api[_\-]?key|secret[_\-]?key|access[_\-]?token|auth[_\-]?token|bearer)["\s:=]+([a-zA-Z0-9_\-]{16,64})', re.IGNORECASE)

JUNK_EMAILS = frozenset({
    "example.com", "test.com", "domain.com", "email.com", "sentry.io",
    "sentry-next.io", "schema.org", "w3.org", "placeholder.com",
})


def _ua():
    return random.choice(USER_AGENTS)


def _clean_email(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    if domain in JUNK_EMAILS:
        return False
    if len(email) > 100:
        return False
    if email.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")):
        return False
    return True


def _clean_phone(phone: str) -> bool:
    digits = re.sub(r'\D', '', phone)
    return 7 <= len(digits) <= 15


def _fetch_page(url: str) -> tuple[str | None, str | None]:
    """Fetch a URL and return (html_content, final_url). Returns (None, None) on failure."""
    headers = {
        "User-Agent":      _ua(),
        "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    attempts = [
        lambda: httpx.get(url, headers=headers, timeout=15, follow_redirects=True, verify=False),
        lambda: httpx.get(url.replace("https://", "http://"), headers=headers, timeout=15, follow_redirects=True, verify=False),
    ]
    for attempt in attempts:
        try:
            r = attempt()
            if r.status_code < 400:
                return r.text, str(r.url)
        except Exception:
            continue
    return None, None


def _extract_all(html: str, base_url: str) -> dict[str, Any]:
    """Deep extract of all OSINT-relevant data from HTML."""
    soup      = BeautifulSoup(html, "html.parser")
    full_text = soup.get_text(separator=" ")
    raw_html  = str(soup)

    # ── Emails ───────────────────────────────────────────────────────────────
    emails = sorted({
        e.lower() for e in EMAIL_RE.findall(raw_html)
        if _clean_email(e)
    })

    # ── Phones ───────────────────────────────────────────────────────────────
    phones_raw = PHONE_RE.findall(full_text)
    phones = sorted({
        p.strip() for p in phones_raw
        if _clean_phone(p)
    })[:20]

    # ── Social profiles ──────────────────────────────────────────────────────
    social_raw = SOCIAL_RE.findall(raw_html)
    socials    = sorted(set(f"https://{s}" if not s.startswith("http") else s for s in social_raw))[:30]

    # ── Meta tags ────────────────────────────────────────────────────────────
    meta: dict[str, str] = {}
    for tag in soup.find_all("meta"):
        name    = tag.get("name", tag.get("property", "")).lower()
        content = tag.get("content", "").strip()
        if name and content and len(content) < 500:
            meta[name] = content

    important_meta = {
        k: v for k, v in meta.items()
        if any(x in k for x in [
            "author", "generator", "description", "og:", "twitter:", "creator",
            "publisher", "owner", "copyright", "robots", "keywords",
        ])
    }

    # ── HTML comments ────────────────────────────────────────────────────────
    comments = []
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        stripped = c.strip()
        if stripped and len(stripped) > 5 and len(stripped) < 500:
            comments.append(stripped)
    comments = comments[:20]

    # ── External links ───────────────────────────────────────────────────────
    ext_links: list[dict[str, str]] = []
    seen_links: set[str] = set()
    base_domain = urlparse(base_url).netloc
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc == base_domain:
            continue
        if full in seen_links:
            continue
        seen_links.add(full)
        text = a.get_text(strip=True)[:80]
        ext_links.append({"url": full, "text": text, "domain": parsed.netloc})
        if len(ext_links) >= 30:
            break

    # ── Technology stack ─────────────────────────────────────────────────────
    tech: list[str] = []
    generator = meta.get("generator", "")
    if generator:
        tech.append(generator)

    scripts = [s.get("src", "") for s in soup.find_all("script", src=True)]
    for src in scripts:
        if "jquery" in src.lower():      tech.append("jQuery")
        if "react" in src.lower():       tech.append("React")
        if "vue" in src.lower():         tech.append("Vue.js")
        if "angular" in src.lower():     tech.append("Angular")
        if "wordpress" in src.lower():   tech.append("WordPress")
        if "shopify" in src.lower():     tech.append("Shopify")
        if "analytics" in src.lower():   tech.append("Google Analytics")
        if "gtag" in src.lower():        tech.append("Google Tag Manager")
        if "facebook" in src.lower():    tech.append("Facebook Pixel")
        if "hotjar" in src.lower():      tech.append("Hotjar")
    tech = sorted(set(tech))[:15]

    # ── API keys / secrets exposed ────────────────────────────────────────────
    exposed_keys: list[str] = []
    for script in soup.find_all("script"):
        script_text = script.get_text()
        for match in API_KEY_RE.finditer(script_text):
            val = match.group(0)[:120]
            if val not in exposed_keys:
                exposed_keys.append(val)
    exposed_keys = exposed_keys[:10]

    # ── Crypto addresses ─────────────────────────────────────────────────────
    crypto = sorted(set(CRYPTO_RE.findall(raw_html)))[:10]

    # ── IP addresses in source ────────────────────────────────────────────────
    ips = sorted(set(
        ip for ip in IPV4_RE.findall(raw_html)
        if not ip.startswith(("127.", "0.", "192.168.", "10.", "172."))
    ))[:10]

    # ── Page title and description ────────────────────────────────────────────
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    description = meta.get("description", meta.get("og:description", ""))

    return {
        "title":        title,
        "description":  description,
        "emails":       emails,
        "phones":       phones,
        "socials":      socials,
        "meta":         important_meta,
        "comments":     comments,
        "ext_links":    ext_links,
        "tech":         tech,
        "exposed_keys": exposed_keys,
        "crypto":       crypto,
        "ips":          ips,
    }


@method_decorator(xframe_options_exempt, name="dispatch")
class InspectView(View):
    """
    GET /api/search/inspect/?url=<url>
    Fetches a URL and extracts all OSINT-relevant data:
    emails, phones, social links, meta tags, HTML comments,
    external links, tech stack, exposed keys, crypto addresses.
    """

    def get(self, request):  # type: ignore[override]
        url = request.GET.get("url", "").strip()
        if not url:
            return JsonResponse({"error": "No URL provided"}, status=400)

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        html, final_url = _fetch_page(url)
        if not html:
            return JsonResponse({"error": "Could not fetch page"}, status=502)

        data = _extract_all(html, final_url or url)
        data["url"]       = final_url or url
        data["source_url"] = url

        # Summary counts for the frontend
        data["summary"] = {
            "emails":       len(data["emails"]),
            "phones":       len(data["phones"]),
            "socials":      len(data["socials"]),
            "ext_links":    len(data["ext_links"]),
            "comments":     len(data["comments"]),
            "exposed_keys": len(data["exposed_keys"]),
            "crypto":       len(data["crypto"]),
        }

        return JsonResponse(data)