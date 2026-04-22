"""
osint_phone.py — Active phone intelligence
Carrier detection, country, WhatsApp, Telegram, reverse lookup links.
"""
import re
import httpx
from typing import Any

TIMEOUT = 7
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def _r(title, link, snippet, source):
    return {"title": title, "link": link, "snippet": snippet,
            "source": source, "osint": True,
            "displayLink": re.sub(r"https?://", "", link).split("/")[0]}

def _clean(q):
    return re.sub(r"[\s\-\.\(\)]", "", q.strip())

def _digits(q):
    return re.sub(r"[^\d]", "", q)


COUNTRY_PREFIXES = {
    "351": ("Portugal", "🇵🇹"), "44": ("United Kingdom", "🇬🇧"),
    "1":   ("USA / Canada", "🇺🇸"), "55": ("Brazil", "🇧🇷"),
    "34":  ("Spain", "🇪🇸"), "49": ("Germany", "🇩🇪"),
    "33":  ("France", "🇫🇷"), "39": ("Italy", "🇮🇹"),
    "7":   ("Russia", "🇷🇺"), "86": ("China", "🇨🇳"),
    "91":  ("India", "🇮🇳"), "81": ("Japan", "🇯🇵"),
    "82":  ("South Korea", "🇰🇷"), "61": ("Australia", "🇦🇺"),
    "52":  ("Mexico", "🇲🇽"), "54": ("Argentina", "🇦🇷"),
    "56":  ("Chile", "🇨🇱"), "57": ("Colombia", "🇨🇴"),
    "31":  ("Netherlands", "🇳🇱"), "32": ("Belgium", "🇧🇪"),
    "41":  ("Switzerland", "🇨🇭"), "46": ("Sweden", "🇸🇪"),
    "47":  ("Norway", "🇳🇴"), "45": ("Denmark", "🇩🇰"),
    "358": ("Finland", "🇫🇮"), "48": ("Poland", "🇵🇱"),
}


def _country_detect(phone):
    digits = _digits(phone)
    for prefix in sorted(COUNTRY_PREFIXES.keys(), key=len, reverse=True):
        if digits.startswith(prefix):
            country, flag = COUNTRY_PREFIXES[prefix]
            return [_r(
                f"Country Identified — {flag} {country} (+{prefix})",
                f"https://countrycode.org/",
                f"Number {phone} uses international prefix +{prefix}, originating from {country}. "
                f"Digits after prefix: {digits[len(prefix):]}",
                "countrycode"
            )]
    return []


def _numverify(phone):
    digits = _digits(phone)
    try:
        r = httpx.get(
            f"https://phonevalidation.abstractapi.com/v1/?api_key=free&phone={digits}",
            timeout=TIMEOUT, headers=H)
        d = r.json()
        if d.get("valid"):
            return [_r(
                f"Phone Validated — {d.get('format',{}).get('international', phone)}",
                f"https://numverify.com/",
                f"Country: {d.get('country',{}).get('name','?')} · "
                f"Carrier: {d.get('carrier','?')} · "
                f"Type: {d.get('type','?')} · "
                f"Local: {d.get('format',{}).get('local','?')}",
                "numverify"
            )]
    except Exception:
        pass
    return []


def _messaging_links(phone):
    digits = _digits(phone)
    clean  = _clean(phone)
    if not digits:
        return []
    intl = digits if digits.startswith(("1","2","3","4","5","6","7","8","9")) else digits
    return [
        _r(f"WhatsApp — +{intl}",
           f"https://wa.me/{intl}",
           f"Direct WhatsApp message link for +{intl}. "
           f"If this number is registered on WhatsApp, this opens a chat directly.",
           "whatsapp"),
        _r(f"Telegram — +{intl}",
           f"https://t.me/+{intl}",
           f"Telegram contact link for +{intl}. "
           f"If registered on Telegram, this resolves to a profile.",
           "telegram"),
        _r(f"Signal — {phone}",
           f"https://signal.me/#p/+{intl}",
           f"Signal profile link for +{intl}. Opens Signal if the number is registered.",
           "signal"),
    ]


def _reverse_lookup(phone):
    digits = _digits(phone)
    return [
        _r(f"Truecaller — {phone}",
           f"https://www.truecaller.com/search/intl/{digits}",
           f"Truecaller crowdsourced caller ID for {phone}: name, carrier, spam score.",
           "truecaller"),
        _r(f"Whitepages — {phone}",
           f"https://www.whitepages.com/phone/{digits}",
           f"Whitepages reverse lookup for {phone}: owner name, address, relatives.",
           "whitepages"),
        _r(f"NumLookup — {phone}",
           f"https://www.numlookup.com/?number={phone}",
           f"NumLookup free reverse phone lookup for {phone}: carrier, country, line type.",
           "numlookup"),
        _r(f"800notes — {phone}",
           f"https://800notes.com/Phone.aspx/{phone}",
           f"Community reports for {phone}: scam alerts, spam, business identification.",
           "800notes"),
        _r(f"WhoCallsMe — {phone}",
           f"https://whocalledme.com/PhoneNumber/{digits}",
           f"User reports for {phone}: who is calling, spam or legitimate.",
           "whocalledme"),
    ]


def _breach_links(phone):
    return [
        _r(f"IntelX — {phone}",
           f"https://intelx.io/?s={phone}",
           f"Intelligence X search: find {phone} in breaches, pastes and leaked databases.",
           "intelx"),
        _r(f"PhoneInfoga — {phone}",
           f"https://demo.phoneinfoga.crvx.fr/#/{_digits(phone)}",
           f"PhoneInfoga open-source scanner for {phone}: carrier, OSINT sources, footprint.",
           "phoneinfoga"),
    ]


def enrich_phone(q: str) -> list[dict[str, Any]]:
    phone = _clean(q)
    out   = []
    out.extend(_country_detect(phone))
    out.extend(_numverify(phone))
    out.extend(_messaging_links(phone))
    out.extend(_reverse_lookup(phone))
    out.extend(_breach_links(phone))
    return out