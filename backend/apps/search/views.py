from __future__ import annotations

import hashlib
import os
import json
import random
import re
import time
import concurrent.futures

# OSINT enrichment scripts — one per target type
try:
    from apps.search.osint_phone    import enrich_phone
    from apps.search.osint_url      import enrich_url
    from apps.search.osint_email    import enrich_email
    from apps.search.osint_username import enrich_username
    from apps.search.osint_person   import enrich_person
    _OSINT_SCRIPTS_AVAILABLE = True
except ImportError:
    _OSINT_SCRIPTS_AVAILABLE = False
from collections import defaultdict
from typing import Any
from urllib.parse import unquote, parse_qs, urlparse, quote_plus

import httpx
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.http import StreamingHttpResponse, JsonResponse
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

BLOCKED_DOMAINS: frozenset[str] = frozenset({
    "zhihu.com","baidu.com","weibo.com","qq.com","taobao.com","jd.com","163.com",
    "sina.com.cn","sohu.com","youku.com","bilibili.com","csdn.net","cnblogs.com",
    "jianshu.com","douban.com","51cto.com","oschina.net","segmentfault.com",
    "v2ex.com","douyin.com","weixin.qq.com","mp.weixin.qq.com","yahoo.co.jp",
    "nicovideo.jp","rakuten.co.jp","ameblo.jp","hatena.ne.jp","naver.com",
    "daum.net","tistory.com","vk.com","yandex.ru","mail.ru","ok.ru","habr.com",
})

NON_LATIN_RE = re.compile(
    r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff\u0900-\u097f]"
)

MAX_PER_DOMAIN = 3
MAX_PER_GROUP  = 25
CACHE_TTL      = 900
GROUP_TIMEOUT  = 35

# Electron search worker — port passed via env var from main.js
WORKER_PORT = int(os.environ.get("FIRECAT_WORKER_PORT", "8766"))

# ---------------------------------------------------------------------------
# OSINT Groups — deep operators, multiple layers per group
# ---------------------------------------------------------------------------

HACKING_GROUPS: list[dict[str, Any]] = [

    # =========================================================================
    # TARGET: PERSON — full name or alias
    # Goal: map complete digital footprint of a real person
    # =========================================================================
    {
        "id": "person_web", "label": "Web Presence", "category": "person",
        "operators": [
            '"{q}"',
            '{q}',
            'intitle:"{q}"',
            '"{q}" -site:amazon.com -site:ebay.com -site:etsy.com',
            '"{q}" profile OR biography OR about OR "about me"',
            '"{q}" interview OR mentioned OR featured OR speaker',
        ],
    },
    {
        "id": "person_social", "label": "Social Networks", "category": "person",
        "operators": [
            '"{q}" site:linkedin.com OR site:twitter.com OR site:x.com OR site:instagram.com OR site:facebook.com OR site:tiktok.com OR site:reddit.com',
            '"{q}" site:about.me OR site:linktree.com OR site:bio.link OR site:beacons.ai OR site:carrd.co',
            '"{q}" site:pinterest.com OR site:tumblr.com OR site:medium.com OR site:substack.com OR site:quora.com',
            '"{q}" site:mastodon.social OR site:threads.net OR site:bluesky.app',
        ],
    },
    {
        "id": "person_linkedin", "label": "LinkedIn Profile", "category": "person",
        "operators": [
            '"{q}" site:linkedin.com',
            '"{q}" site:linkedin.com/in/',
            'site:linkedin.com "{q}" profile OR experience OR education',
            'site:linkedin.com/pub/ "{q}"',
        ],
    },
    {
        "id": "person_facebook", "label": "Facebook", "category": "person",
        "operators": [
            '"{q}" site:facebook.com',
            'site:facebook.com/people/ "{q}"',
            'site:facebook.com "{q}" profile OR timeline OR photos',
            '"{q}" site:facebook.com -site:facebook.com/groups/',
        ],
    },
    {
        "id": "person_instagram", "label": "Instagram", "category": "person",
        "operators": [
            '"{q}" site:instagram.com',
            'site:instagram.com "@{q}"',
            'site:instagram.com "{q}" photos OR tagged',
        ],
    },
    {
        "id": "person_twitter", "label": "Twitter / X", "category": "person",
        "operators": [
            '"{q}" site:twitter.com OR site:x.com',
            'site:twitter.com "{q}"',
            'site:x.com "{q}"',
            '"@{q}" site:twitter.com OR site:x.com',
        ],
    },
    {
        "id": "person_youtube", "label": "YouTube", "category": "person",
        "operators": [
            '"{q}" site:youtube.com',
            'site:youtube.com/channel/ "{q}"',
            'site:youtube.com "@{q}"',
            'site:youtube.com "{q}" videos OR channel OR about',
        ],
    },
    {
        "id": "person_tiktok", "label": "TikTok", "category": "person",
        "operators": [
            '"{q}" site:tiktok.com',
            'site:tiktok.com "@{q}"',
            'site:tiktok.com "{q}" creator OR videos',
        ],
    },
    {
        "id": "person_news", "label": "News & Press", "category": "person",
        "operators": [
            '"{q}" site:reuters.com OR site:bbc.com OR site:theguardian.com OR site:apnews.com OR site:cnn.com OR site:forbes.com',
            '"{q}" site:nytimes.com OR site:wsj.com OR site:bloomberg.com OR site:ft.com OR site:economist.com',
            '"{q}" news article interview press mentioned journalist',
            'inurl:news "{q}" OR inurl:article "{q}"',
        ],
    },
    {
        "id": "person_images", "label": "Photos & Images", "category": "person",
        "operators": [
            '"{q}" filetype:jpg OR filetype:jpeg OR filetype:png',
            '"{q}" site:flickr.com OR site:500px.com OR site:imgur.com',
            '"{q}" photo OR portrait OR headshot OR picture -site:shutterstock.com -site:getty.com',
            '"{q}" site:google.com/maps/contrib OR site:maps.google.com',
        ],
    },
    {
        "id": "person_cv", "label": "CV & Resume", "category": "person",
        "operators": [
            '"{q}" filetype:pdf inurl:cv OR inurl:resume OR inurl:curriculum',
            '"{q}" "curriculum vitae" OR "resume" filetype:pdf OR filetype:doc',
            '"{q}" site:visualcv.com OR site:resume.io OR site:rxresu.me OR site:kickresume.com',
            'intitle:"resume" OR intitle:"curriculum vitae" "{q}"',
        ],
    },
    {
        "id": "person_academic", "label": "Academic & Research", "category": "person",
        "operators": [
            '"{q}" site:researchgate.net OR site:academia.edu OR site:arxiv.org OR site:orcid.org',
            '"{q}" site:scholar.google.com OR site:pubmed.ncbi.nlm.nih.gov OR site:semanticscholar.org',
            '"{q}" author researcher professor phd thesis dissertation publication',
        ],
    },
    {
        "id": "person_github", "label": "GitHub / Code", "category": "person",
        "operators": [
            '"{q}" site:github.com',
            'site:github.com "{q}" profile OR README OR contributions',
            'site:gitlab.com OR site:bitbucket.org "{q}"',
        ],
    },
    {
        "id": "person_business", "label": "Business & Company", "category": "person",
        "operators": [
            '"{q}" site:crunchbase.com OR site:bloomberg.com OR site:zoominfo.com',
            '"{q}" CEO OR founder OR director OR "board member" OR executive OR "co-founder"',
            '"{q}" site:angel.co OR site:wellfound.com OR site:f6s.com',
            '"{q}" company OR startup OR business OR venture OR investor',
        ],
    },
    {
        "id": "person_location", "label": "Location & Address", "category": "person",
        "operators": [
            '"{q}" "lives in" OR "based in" OR "located in" OR "from" OR hometown OR "grew up"',
            '"{q}" address OR street OR city OR neighbourhood OR "zip code" OR "postal code"',
            '"{q}" site:whitepages.com OR site:spokeo.com OR site:fastpeoplesearch.com',
            '"{q}" site:maps.google.com OR coordinates OR location',
        ],
    },
    {
        "id": "person_records", "label": "Public Records", "category": "person",
        "operators": [
            '"{q}" "public record" OR "court record" OR "criminal record" OR "arrest record"',
            '"{q}" "property record" OR "voter registration" OR "marriage record" OR "divorce record"',
            '"{q}" "bankruptcy" OR "lawsuit" OR "judgment" site:gov OR site:court',
            '"{q}" site:peekyou.com OR site:intelius.com OR site:beenverified.com OR site:radaris.com',
        ],
    },
    {
        "id": "person_paste", "label": "Pastes & Leaks", "category": "person",
        "operators": [
            '"{q}" site:pastebin.com OR site:gist.github.com OR site:paste.ee OR site:justpaste.it',
            '"{q}" site:hastebin.com OR site:rentry.co OR site:dpaste.org OR site:privatebin.net',
            '"{q}" "data breach" OR leaked OR "found in" OR "appeared in" breach',
        ],
    },

    # =========================================================================
    # TARGET: USERNAME — social handle or platform username
    # Goal: find all accounts using this exact username across platforms
    # =========================================================================
    {
        "id": "username_exact", "label": "Exact Username Match", "category": "username",
        "operators": [
            '"{q}"',
            '{q}',
            '"@{q}"',
            'inurl:{q}',
            'intitle:{q}',
        ],
    },
    {
        "id": "username_social", "label": "Social Media Accounts", "category": "username",
        "operators": [
            'site:twitter.com/{q} OR site:x.com/{q}',
            'site:instagram.com/{q}',
            'site:facebook.com/{q}',
            'site:tiktok.com/@{q}',
            'site:reddit.com/u/{q} OR site:reddit.com/user/{q}',
            'site:youtube.com/@{q} OR site:youtube.com/c/{q}',
        ],
    },
    {
        "id": "username_dev", "label": "Developer Platforms", "category": "username",
        "operators": [
            'site:github.com/{q}',
            'site:gitlab.com/{q}',
            'site:stackoverflow.com/users/ "{q}"',
            'site:dev.to/{q} OR site:hashnode.com/@{q}',
            'site:npmjs.com/~{q} OR site:pypi.org/user/{q}',
            'site:codepen.io/{q} OR site:jsfiddle.net/user/{q}',
        ],
    },
    {
        "id": "username_gaming", "label": "Gaming Platforms", "category": "username",
        "operators": [
            'site:steamcommunity.com/id/{q} OR site:steamcommunity.com/profiles/ "{q}"',
            'site:twitch.tv/{q}',
            'site:discord.com OR site:discord.gg "{q}"',
            '"{q}" site:xbox.com OR site:playstation.com OR site:epicgames.com',
            'site:faceit.com/en/ "{q}" OR site:tracker.gg "{q}"',
        ],
    },
    {
        "id": "username_content", "label": "Content & Creative", "category": "username",
        "operators": [
            'site:medium.com/@{q} OR site:substack.com/@{q}',
            'site:patreon.com/{q} OR site:ko-fi.com/{q} OR site:buymeacoffee.com/{q}',
            'site:behance.net/{q} OR site:dribbble.com/{q} OR site:artstation.com/{q}',
            'site:soundcloud.com/{q} OR site:bandcamp.com/{q} OR site:last.fm/user/{q}',
            'site:deviantart.com/{q} OR site:pixiv.net/ "{q}"',
        ],
    },
    {
        "id": "username_paste", "label": "Pastes & Leaks", "category": "username",
        "operators": [
            'site:pastebin.com "{q}" OR site:gist.github.com "{q}"',
            '"{q}" site:haveibeenpwned.com OR site:dehashed.com OR "data breach"',
            '"{q}" leaked OR "found in breach" OR compromised OR credential',
            '"{q}" site:leakcheck.io OR site:snusbase.com OR site:breachdirectory.org',
        ],
    },
    {
        "id": "username_osint", "label": "Username OSINT Tools", "category": "username",
        "operators": [
            '"{q}" site:namechk.com OR site:checkusernames.com OR site:knowem.com',
            '"{q}" site:usersearch.org OR site:whatsmyname.app OR site:socialscan.io',
            '"{q}" site:sherlock.pm OR site:namecheckr.com',
            '"username" "{q}" profile OR account OR registered',
        ],
    },
    {
        "id": "username_web", "label": "General Web Mentions", "category": "username",
        "operators": [
            '"@{q}" email OR contact OR social',
            'inurl:"{q}" -site:amazon.com -site:ebay.com',
            '"{q}" username OR handle OR account OR "user profile"',
            '"{q}" joined OR registered OR "member since"',
        ],
    },

    # =========================================================================
    # TARGET: EMAIL — email address
    # Goal: find who owns this email, where it appears, what accounts it has
    # =========================================================================
    {
        "id": "email_exact", "label": "Email Direct Search", "category": "email",
        "operators": [
            '"{q}"',
            '{q}',
            'intext:"{q}"',
            'intitle:"{q}"',
        ],
    },
    {
        "id": "email_breach", "label": "Data Breaches", "category": "email",
        "operators": [
            '"{q}" site:haveibeenpwned.com',
            '"{q}" site:dehashed.com OR site:leakcheck.io OR site:snusbase.com',
            '"{q}" "data breach" OR "data leak" OR leaked OR compromised OR "found in"',
            '"{q}" site:breachdirectory.org OR site:leak-lookup.com',
        ],
    },
    {
        "id": "email_social", "label": "Social Media", "category": "email",
        "operators": [
            '"{q}" site:linkedin.com OR site:twitter.com OR site:facebook.com OR site:instagram.com',
            '"{q}" site:github.com OR site:gitlab.com OR site:stackoverflow.com',
            '"{q}" profile OR account OR "sign up" OR registered OR "member"',
        ],
    },
    {
        "id": "email_paste", "label": "Pastes & Exposed", "category": "email",
        "operators": [
            '"{q}" site:pastebin.com OR site:gist.github.com OR site:paste.ee',
            '"{q}" site:justpaste.it OR site:hastebin.com OR site:rentry.co',
            '"{q}" filetype:txt OR filetype:csv OR filetype:log',
        ],
    },
    {
        "id": "email_domain", "label": "Domain & WHOIS", "category": "email",
        "operators": [
            '"{q}" whois OR registrant OR "domain owner" OR "registered by"',
            '"{q}" site:whois.domaintools.com OR site:who.is OR site:whois.net',
            '"{q}" site:viewdns.info OR site:hunter.io OR site:emailrep.io',
        ],
    },
    {
        "id": "email_docs", "label": "Documents & Files", "category": "email",
        "operators": [
            '"{q}" filetype:pdf',
            '"{q}" filetype:doc OR filetype:docx OR filetype:xls OR filetype:xlsx',
            '"{q}" filetype:json OR filetype:xml OR filetype:csv',
            'intitle:"index of" "{q}"',
        ],
    },
    {
        "id": "email_osint", "label": "OSINT Aggregators", "category": "email",
        "operators": [
            '"{q}" site:hunter.io OR site:emailrep.io OR site:trumail.io',
            '"{q}" site:intelx.io OR site:epieos.com OR site:ghunt.io',
            '"{q}" site:pipl.com OR site:spokeo.com OR site:beenverified.com',
            '"email" "{q}" owner OR person OR identity OR name',
        ],
    },
    {
        "id": "email_forums", "label": "Forums & Communities", "category": "email",
        "operators": [
            '"{q}" site:reddit.com OR site:quora.com OR site:stackoverflow.com',
            '"{q}" site:discourse.org OR forum OR community OR board',
            '"{q}" "contact" OR "reach me" OR "email me" OR "get in touch"',
        ],
    },

    # =========================================================================
    # TARGET: PHONE — phone number
    # Goal: identify owner, location, linked accounts
    # =========================================================================
    {
        "id": "phone_exact", "label": "Phone Direct Search", "category": "phone",
        "operators": [
            '"{q}"',
            '{q}',
            'intext:"{q}"',
            '"{q}" phone OR telephone OR mobile OR contact OR call',
        ],
    },
    {
        "id": "phone_reverse", "label": "Reverse Lookup", "category": "phone",
        "operators": [
            '"{q}" site:whitepages.com OR site:spokeo.com OR site:truecaller.com',
            '"{q}" site:numverify.com OR site:phoneinfoga.io OR site:callerinfo.com',
            '"{q}" site:411.com OR site:reversephonelookup.com OR site:zlookup.com',
            '"reverse lookup" "{q}" OR "who called" "{q}" OR "phone owner" "{q}"',
        ],
    },
    {
        "id": "phone_messaging", "label": "WhatsApp & Messaging", "category": "phone",
        "operators": [
            '"wa.me/{q}" OR "api.whatsapp.com/send?phone={q}"',
            '"{q}" whatsapp OR telegram OR signal OR viber',
            'site:t.me OR site:wa.me "{q}"',
            '"{q}" "t.me/" OR "telegram.me/" OR "join my channel"',
        ],
    },
    {
        "id": "phone_social", "label": "Social & Profiles", "category": "phone",
        "operators": [
            '"{q}" site:facebook.com OR site:linkedin.com OR site:twitter.com',
            '"{q}" site:truepeoplesearch.com OR site:fastpeoplesearch.com OR site:beenverified.com',
            '"{q}" profile OR contact OR "get in touch" OR bio',
        ],
    },
    {
        "id": "phone_paste", "label": "Pastes & Leaks", "category": "phone",
        "operators": [
            '"{q}" site:pastebin.com OR site:gist.github.com OR site:paste.ee',
            '"{q}" "data breach" OR leaked OR exposed OR "found in"',
            '"{q}" filetype:txt OR filetype:csv OR filetype:log',
        ],
    },
    {
        "id": "phone_records", "label": "Public Records", "category": "phone",
        "operators": [
            '"{q}" "public record" OR "court record" OR site:gov',
            '"{q}" address OR owner OR registered OR "belongs to"',
            '"{q}" site:peekyou.com OR site:intelius.com OR site:radaris.com',
        ],
    },

    # =========================================================================
    # TARGET: DOMAIN — website domain
    # Goal: owner, infrastructure, content, history, vulnerabilities
    # =========================================================================
    {
        "id": "domain_whois", "label": "WHOIS & Registration", "category": "domain",
        "operators": [
            '"{q}" site:whois.domaintools.com OR site:who.is OR site:whois.net',
            '"{q}" whois OR registrant OR "domain owner" OR "registered by" OR nameserver',
            '"{q}" site:viewdns.info OR site:centralops.net OR site:mxtoolbox.com',
            'site:dnsdumpster.com "{q}" OR site:shodan.io "{q}"',
        ],
    },
    {
        "id": "domain_certs", "label": "SSL Certificates", "category": "domain",
        "operators": [
            '"{q}" site:crt.sh OR site:censys.io OR site:shodan.io',
            '"{q}" certificate OR ssl OR tls OR "subdomain"',
            'site:crt.sh "%.{q}"',
        ],
    },
    {
        "id": "domain_tech", "label": "Technology Stack", "category": "domain",
        "operators": [
            '"{q}" site:builtwith.com OR site:wappalyzer.com OR site:w3techs.com',
            '"{q}" site:similarweb.com OR site:semrush.com OR site:ahrefs.com',
            '"{q}" powered by OR "built with" OR technology OR stack OR framework',
        ],
    },
    {
        "id": "domain_exposed", "label": "Exposed Files & Dirs", "category": "domain",
        "operators": [
            'site:{q} intitle:"index of"',
            'site:{q} filetype:pdf OR filetype:xls OR filetype:sql OR filetype:env',
            'site:{q} inurl:admin OR inurl:login OR inurl:backup OR inurl:config',
            'site:{q} inurl:".env" OR inurl:"wp-config" OR inurl:".git"',
        ],
    },
    {
        "id": "domain_emails", "label": "Emails on Domain", "category": "domain",
        "operators": [
            '"@{q}" email OR contact OR mailto',
            'site:{q} "contact" OR "email" OR "@{q}"',
            '"{q}" site:hunter.io OR site:snov.io OR site:voilanorbert.com',
            'intext:"@{q}" filetype:pdf OR filetype:txt OR filetype:csv',
        ],
    },
    {
        "id": "domain_archive", "label": "History & Archive", "category": "domain",
        "operators": [
            '"{q}" site:web.archive.org',
            'site:web.archive.org/web/ "{q}"',
            '"{q}" site:archive.org OR "wayback machine" OR "cached version"',
        ],
    },
    {
        "id": "domain_mentions", "label": "Web Mentions", "category": "domain",
        "operators": [
            '"{q}" -site:{q}',
            'link:{q} OR "links to {q}"',
            '"{q}" mentioned OR referenced OR review OR backlink',
            '"{q}" site:reddit.com OR site:hackernews.com OR site:twitter.com',
        ],
    },
    {
        "id": "domain_subdomains", "label": "Subdomains & Infrastructure", "category": "domain",
        "operators": [
            'site:*.{q}',
            '"{q}" subdomain OR "sub-domain" OR "*.{q}"',
            '"{q}" site:hackertarget.com OR site:dnsdumpster.com OR site:spyse.com',
            'inurl:{q} -site:{q}',
        ],
    },
]

GROUP_BY_ID: dict[str, dict[str, Any]] = {g["id"]: g for g in HACKING_GROUPS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ua() -> str:
    return random.choice(USER_AGENTS)


def _headers(referer: str = "") -> dict[str, str]:
    h = {
        "User-Agent":      _ua(),
        "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "DNT":             "1",
        "Connection":      "keep-alive",
    }
    if referer:
        h["Referer"] = referer
    return h


def _normalise_cache_key(q: str) -> str:
    words = sorted(q.lower().split())
    return "deep4_" + hashlib.md5(" ".join(words).encode()).hexdigest()


def _clean_display(link: str) -> str:
    try:
        return urlparse(link).netloc.replace("www.", "")
    except Exception:
        return link


def _get_domain(link: str) -> str:
    try:
        return urlparse(link).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _is_blocked(link: str) -> bool:
    domain = _get_domain(link)
    return any(domain == b or domain.endswith("." + b) for b in BLOCKED_DOMAINS)


def _is_english(item: dict[str, Any]) -> bool:
    if _is_blocked(item.get("link", "")):
        return False
    text      = f"{item.get('title', '')} {item.get('snippet', '')}"
    non_latin = len(NON_LATIN_RE.findall(text))
    total     = len([c for c in text if c.strip()])
    return not (total > 0 and non_latin / total > 0.25)


def _deduplicate(
    items: list[dict[str, Any]],
    q_words: list[str] | set[str],
    strict: bool = False,
) -> list[dict[str, Any]]:
    seen_urls:    set[str]             = set()
    domain_count: dict[str, int]       = defaultdict(int)
    final:        list[dict[str, Any]] = []

    for item in items:
        url = item.get("link", "")
        if not url or url in seen_urls:
            continue
        if not item.get("title", "").strip():
            continue
        if not item.get("osint") and not _is_english(item):
            continue

        domain = _get_domain(url)
        if domain_count[domain] >= MAX_PER_DOMAIN:
            continue

        # OSINT enrichment results bypass the relevance filter — they are curated
        if item.get("osint"):
            seen_urls.add(url)
            domain_count[domain] += 1
            final.append(item)
            if len(final) >= MAX_PER_GROUP:
                break
            continue

        # Relevance filter — respects word order, allows non-contiguous matches
        if q_words:
            q_list   = list(q_words)  # already ordered — from q.split()
            q_phrase = " ".join(q_list)       # exact phrase e.g. "andres nicolas"
            text     = f"{item.get('title','')} {item.get('snippet','')} {url}".lower()

            # Accept if exact phrase present
            if q_phrase in text:
                pass  # accepted
            else:
                # All words must be present AND in correct order
                # Find each word's position — must be ascending
                positions = []
                search_from = 0
                ok = True
                for w in q_list:
                    idx = text.find(w, search_from)
                    if idx == -1:
                        ok = False
                        break
                    positions.append(idx)
                    search_from = idx + 1
                if not ok:
                    continue
                # Reject if words are too far apart (> 80 chars gap) — avoids false positives
                if len(positions) >= 2:
                    span = positions[-1] - positions[0]
                    if span > 80:
                        continue

        seen_urls.add(url)
        domain_count[domain] += 1
        final.append(item)

        if len(final) >= MAX_PER_GROUP:
            break

    return final


# ---------------------------------------------------------------------------
# Open APIs — no key required, reliable JSON responses
# ---------------------------------------------------------------------------

def _api_github_search(q: str) -> list[dict[str, Any]]:
    """GitHub public search — users, repos, code."""
    items: list[dict[str, Any]] = []
    try:
        # User search
        r = httpx.get(
            "https://api.github.com/search/users",
            params={"q": q, "per_page": "10"},
            headers={"Accept": "application/vnd.github+json", "User-Agent": _ua()},
            timeout=10,
        )
        if r.status_code == 200:
            for user in r.json().get("items", []):
                items.append({
                    "title":       f"{user.get('login')} — GitHub User",
                    "link":        user.get("html_url", ""),
                    "displayLink": "github.com",
                    "snippet":     f"GitHub user · {user.get('type', 'User')} · {user.get('html_url','')}",
                    "source":      "github_api",
                })
        # Repo search
        r2 = httpx.get(
            "https://api.github.com/search/repositories",
            params={"q": q, "per_page": "10", "sort": "stars"},
            headers={"Accept": "application/vnd.github+json", "User-Agent": _ua()},
            timeout=10,
        )
        if r2.status_code == 200:
            for repo in r2.json().get("items", []):
                items.append({
                    "title":       f"{repo.get('full_name')} — GitHub Repository",
                    "link":        repo.get("html_url", ""),
                    "displayLink": "github.com",
                    "snippet":     repo.get("description") or f"⭐ {repo.get('stargazers_count',0)} · {repo.get('language','')}",
                    "source":      "github_api",
                })
    except Exception:
        pass
    return items


def _api_reddit_search(q: str) -> list[dict[str, Any]]:
    """Reddit JSON API — posts and users."""
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://www.reddit.com/search.json",
            params={"q": q, "limit": "15", "sort": "relevance", "type": "link"},
            headers={"User-Agent": f"FirecatOSINT/1.0 {_ua()}"},
            timeout=12, follow_redirects=True,
        )
        if r.status_code == 200:
            for post in r.json().get("data", {}).get("children", []):
                d = post.get("data", {})
                items.append({
                    "title":       d.get("title", ""),
                    "link":        f"https://reddit.com{d.get('permalink','')}",
                    "displayLink": f"reddit.com/r/{d.get('subreddit','')}",
                    "snippet":     d.get("selftext", "")[:200] or f"r/{d.get('subreddit','')} · {d.get('score',0)} upvotes",
                    "source":      "reddit_api",
                })
        # User search
        r2 = httpx.get(
            f"https://www.reddit.com/user/{q}/about.json",
            headers={"User-Agent": f"FirecatOSINT/1.0 {_ua()}"},
            timeout=8,
        )
        if r2.status_code == 200:
            d = r2.json().get("data", {})
            if d.get("name"):
                items.insert(0, {
                    "title":       f"u/{d['name']} — Reddit User",
                    "link":        f"https://reddit.com/user/{d['name']}",
                    "displayLink": "reddit.com",
                    "snippet":     f"Reddit user · {d.get('link_karma',0)} link karma · {d.get('comment_karma',0)} comment karma",
                    "source":      "reddit_api",
                })
    except Exception:
        pass
    return items


def _api_crtsh(q: str) -> list[dict[str, Any]]:
    """crt.sh — SSL certificate transparency logs. Finds domains, subdomains, emails."""
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://crt.sh/",
            params={"q": q, "output": "json"},
            headers={"User-Agent": _ua()},
            timeout=12,
        )
        if r.status_code == 200:
            seen: set[str] = set()
            for cert in r.json()[:30]:
                name = cert.get("name_value", "").strip()
                issuer = cert.get("issuer_name", "")
                logged = cert.get("entry_timestamp", "")[:10]
                for line in name.splitlines():
                    line = line.strip().lstrip("*.")
                    if not line or line in seen:
                        continue
                    seen.add(line)
                    link = f"https://{line}" if not line.startswith("http") else line
                    items.append({
                        "title":       f"{line} — SSL Certificate",
                        "link":        link,
                        "displayLink": line,
                        "snippet":     f"SSL cert logged {logged} · Issuer: {issuer[:60] if issuer else 'unknown'}",
                        "source":      "crt.sh",
                    })
    except Exception:
        pass
    return items


def _api_wayback(q: str) -> list[dict[str, Any]]:
    """Wayback Machine CDX API — historical snapshots of a domain/URL."""
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://web.archive.org/cdx/search/cdx",
            params={
                "url":       f"*.{q}/*" if "." in q else f"*{q}*",
                "output":    "json",
                "limit":     "20",
                "fl":        "original,timestamp,statuscode,mimetype",
                "filter":    "statuscode:200",
                "collapse":  "urlkey",
            },
            headers={"User-Agent": _ua()},
            timeout=14,
        )
        if r.status_code == 200:
            rows = r.json()
            if rows and len(rows) > 1:
                for row in rows[1:21]:
                    original, ts, status, mime = row[0], row[1], row[2], row[3]
                    year = ts[:4] if ts else "?"
                    archived_url = f"https://web.archive.org/web/{ts}/{original}"
                    items.append({
                        "title":       f"[{year}] {original}",
                        "link":        archived_url,
                        "displayLink": "web.archive.org",
                        "snippet":     f"Archived snapshot from {year} · {mime} · Original: {original[:80]}",
                        "source":      "wayback",
                    })
    except Exception:
        pass
    return items


def _api_hackertarget_dns(q: str) -> list[dict[str, Any]]:
    """HackerTarget — DNS lookup, reverse IP, host search."""
    items: list[dict[str, Any]] = []
    try:
        # Host search
        r = httpx.get(
            "https://api.hackertarget.com/hostsearch/",
            params={"q": q},
            headers={"User-Agent": _ua()},
            timeout=10,
        )
        if r.status_code == 200 and "error" not in r.text.lower()[:50]:
            for line in r.text.strip().splitlines()[:20]:
                parts = line.split(",")
                if len(parts) >= 2:
                    hostname, ip = parts[0].strip(), parts[1].strip()
                    items.append({
                        "title":       f"{hostname} → {ip}",
                        "link":        f"https://{hostname}",
                        "displayLink": hostname,
                        "snippet":     f"DNS record · Host: {hostname} · IP: {ip}",
                        "source":      "hackertarget",
                    })
    except Exception:
        pass
    return items


def _api_urlscan(q: str) -> list[dict[str, Any]]:
    """urlscan.io public search — website scans, technologies, contacts."""
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://urlscan.io/api/v1/search/",
            params={"q": q, "size": "15"},
            headers={"User-Agent": _ua(), "Accept": "application/json"},
            timeout=12,
        )
        if r.status_code == 200:
            for result in r.json().get("results", []):
                page = result.get("page", {})
                task = result.get("task", {})
                url  = page.get("url", task.get("url", ""))
                if not url:
                    continue
                items.append({
                    "title":       page.get("title") or url,
                    "link":        f"https://urlscan.io/result/{result.get('task',{}).get('uuid','')}",
                    "displayLink": page.get("domain", _clean_display(url)),
                    "snippet":     f"Scanned: {task.get('time','')[:10]} · {url[:100]}",
                    "source":      "urlscan.io",
                })
    except Exception:
        pass
    return items



# ---------------------------------------------------------------------------
# Electron Worker — real browser searches via the invisible BrowserWindow
# ---------------------------------------------------------------------------

def _parse_google_html(html: str) -> list[dict[str, Any]]:
    """Parse Google SERP HTML extracted from the Electron worker."""
    items: list[dict[str, Any]] = []
    soup = BeautifulSoup(html, "html.parser")

    # Google result containers
    for result in soup.select("div.g, div[data-hveid], div.tF2Cxc, div.yuRUbf"):
        title_el   = result.select_one("h3")
        link_el    = result.select_one("a[href]")
        snippet_el = (
            result.select_one("div.VwiC3b")
            or result.select_one("span.st")
            or result.select_one("div[data-sncf]")
            or result.select_one("div.IsZvec")
        )
        if not title_el or not link_el:
            continue
        link = link_el.get("href", "")
        if not link or not link.startswith("http") or "google.com" in link:
            continue
        items.append({
            "title":       title_el.get_text(strip=True),
            "link":        link,
            "displayLink": _clean_display(link),
            "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
            "source":      "google",
        })

    return items


def _parse_bing_html(html: str) -> list[dict[str, Any]]:
    """Parse Bing SERP HTML from Electron worker (richer than HTTP scraping)."""
    items: list[dict[str, Any]] = []
    soup = BeautifulSoup(html, "html.parser")
    for result in soup.select("li.b_algo"):
        title_el   = result.select_one("h2 a")
        snippet_el = result.select_one(".b_caption p") or result.select_one("p")
        if not title_el:
            continue
        link = title_el.get("href", "")
        if not link or not link.startswith("http") or "bing.com" in link:
            continue
        items.append({
            "title":       title_el.get_text(strip=True),
            "link":        link,
            "displayLink": _clean_display(link),
            "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
            "source":      "bing_electron",
        })
    return items


def _parse_ddg_html(html: str) -> list[dict[str, Any]]:
    """Parse DuckDuckGo HTML from Electron worker."""
    items: list[dict[str, Any]] = []
    soup = BeautifulSoup(html, "html.parser")
    for result in soup.select(".result"):
        title_el   = result.select_one(".result__title a") or result.select_one("a.result__a")
        snippet_el = result.select_one(".result__snippet")
        url_el     = result.select_one(".result__url")
        if not title_el:
            continue
        link = title_el.get("href", "")
        if "uddg=" in link:
            try:
                link = unquote(parse_qs(urlparse(link).query).get("uddg", [""])[0])
            except Exception:
                pass
        if not link or not link.startswith("http"):
            continue
        display = url_el.get_text(strip=True) if url_el else _clean_display(link)
        items.append({
            "title":       title_el.get_text(strip=True),
            "link":        link,
            "displayLink": display.replace("www.", ""),
            "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
            "source":      "ddg_electron",
        })
    return items


def _fetch_electron_worker(engine: str, query: str) -> list[dict[str, Any]]:
    """
    Send a search request to the Electron worker server running on localhost.
    The worker uses a real invisible BrowserWindow — bypasses all bot detection.
    """
    try:
        r = httpx.post(
            f"http://127.0.0.1:{WORKER_PORT}/search",
            json={"engine": engine, "query": query},
            timeout=25,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        html = data.get("html", "")
        if not html:
            return []

        if engine == "google":
            return _parse_google_html(html)
        elif engine == "bing":
            return _parse_bing_html(html)
        elif engine in ("ddg", "duckduckgo"):
            return _parse_ddg_html(html)
        else:
            return _parse_google_html(html)

    except Exception:
        return []


def _is_worker_available() -> bool:
    """Check if the Electron worker server is running via TCP socket check."""
    import socket
    try:
        sock = socket.create_connection(("127.0.0.1", WORKER_PORT), timeout=1)
        sock.close()
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Classic scraping engines
# ---------------------------------------------------------------------------

def _fetch_bing(q: str, pages: int = 4) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cookies = {
        "MUID": "1", "_EDGE_S": "mkt=en-US&ui=en-US&setmkt=en-US&setlang=en-US",
        "_EDGE_V": "1", "SRCHD": "AF=NOFORM", "SRCHUID": "V=2",
        "SRCHUSR": "DOB=20200101", "ENSEARCH": "BENVER=1",
    }
    for first in range(1, pages * 10 + 1, 10):
        try:
            r = httpx.get(
                "https://www.bing.com/search",
                params={"q": q, "setlang": "en-US", "cc": "US", "mkt": "en-US",
                        "ensearch": "1", "first": str(first), "count": "10"},
                headers=_headers("https://www.bing.com/"),
                cookies=cookies, timeout=12, follow_redirects=True,
            )
            if r.status_code != 200:
                break
            soup    = BeautifulSoup(r.text, "html.parser")
            results = soup.select("li.b_algo")
            if not results:
                break
            added = 0
            for result in results:
                title_el   = result.select_one("h2 a")
                snippet_el = result.select_one(".b_caption p") or result.select_one("p")
                cite_el    = result.select_one("cite")
                if not title_el:
                    continue
                link = title_el.get("data-href", "") or title_el.get("href", "")
                if not link or "bing.com" in link:
                    if cite_el:
                        raw  = cite_el.get_text(strip=True).split(" ›")[0].strip()
                        link = ("https://" + raw) if not raw.startswith("http") else raw
                    else:
                        continue
                if not link or not link.startswith("http") or "bing.com" in link:
                    continue
                items.append({
                    "title":       title_el.get_text(strip=True),
                    "link":        link,
                    "displayLink": _clean_display(link),
                    "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
                    "source":      "bing",
                })
                added += 1
            if added == 0:
                break
            time.sleep(random.uniform(0.15, 0.4))
        except Exception:
            break
    return items


def _fetch_duckduckgo(q: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": q, "kl": "en-us", "kp": "-1", "k1": "-1"},
            headers=_headers("https://duckduckgo.com/"),
            timeout=14, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, "html.parser")
        for result in soup.select(".result"):
            title_el   = result.select_one(".result__title a") or result.select_one("a.result__a")
            snippet_el = result.select_one(".result__snippet")
            url_el     = result.select_one(".result__url")
            if not title_el:
                continue
            link = title_el.get("href", "")
            if "uddg=" in link:
                try:
                    link = unquote(parse_qs(urlparse(link).query).get("uddg", [""])[0])
                except Exception:
                    pass
            if not link or not link.startswith("http"):
                continue
            display = url_el.get_text(strip=True) if url_el else _clean_display(link)
            items.append({
                "title":       title_el.get_text(strip=True),
                "link":        link,
                "displayLink": display.replace("www.", ""),
                "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
                "source":      "duckduckgo",
            })
    except Exception:
        pass
    return items


def _fetch_brave(q: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://search.brave.com/search",
            params={"q": q, "source": "web", "lang": "en", "country": "us"},
            headers=_headers("https://search.brave.com/"),
            timeout=14, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, "html.parser")
        for result in soup.select("div.snippet"):
            title_el   = result.select_one(".snippet-title") or result.select_one("span.title")
            snippet_el = result.select_one(".snippet-description") or result.select_one("p")
            link_el    = result.select_one("a[href]")
            if not link_el:
                continue
            link = link_el.get("href", "")
            if not link or not link.startswith("http") or "brave.com" in link:
                continue
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            items.append({
                "title":       title,
                "link":        link,
                "displayLink": _clean_display(link),
                "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
                "source":      "brave",
            })
    except Exception:
        pass
    return items


def _fetch_startpage(q: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://www.startpage.com/sp/search",
            params={"q": q, "language": "english", "cat": "web"},
            headers=_headers("https://www.startpage.com/"),
            timeout=14, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, "html.parser")
        for result in soup.select(".w-gl__result, .result"):
            title_el   = result.select_one("h3 a") or result.select_one("a.result-title")
            snippet_el = result.select_one("p.w-gl__description") or result.select_one(".description")
            if not title_el:
                continue
            link = title_el.get("href", "")
            if not link or not link.startswith("http") or "startpage.com" in link:
                continue
            items.append({
                "title":       title_el.get_text(strip=True),
                "link":        link,
                "displayLink": _clean_display(link),
                "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
                "source":      "startpage",
            })
    except Exception:
        pass
    return items


def _fetch_mojeek(q: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://www.mojeek.com/search",
            params={"q": q, "lang": "en", "country": "US"},
            headers=_headers("https://www.mojeek.com/"),
            timeout=12, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, "html.parser")
        for result in soup.select("ul.results-standard li"):
            title_el   = result.select_one("a.title")
            snippet_el = result.select_one("p.s")
            url_el     = result.select_one("a.ob")
            if not title_el:
                continue
            link = title_el.get("href", "")
            if not link or not link.startswith("http"):
                continue
            items.append({
                "title":       title_el.get_text(strip=True),
                "link":        link,
                "displayLink": url_el.get_text(strip=True).replace("www.", "") if url_el else _clean_display(link),
                "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
                "source":      "mojeek",
            })
    except Exception:
        pass
    return items


def _fetch_yahoo(q: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        r = httpx.get(
            "https://search.yahoo.com/search",
            params={"p": q, "ei": "UTF-8", "n": "20", "fl": "1", "vl": "lang_en"},
            headers=_headers("https://search.yahoo.com/"),
            timeout=12, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, "html.parser")
        for result in soup.select("div.algo, div.Sr"):
            title_el   = result.select_one("h3 a") or result.select_one("h3.title a")
            snippet_el = result.select_one("p") or result.select_one(".compText")
            if not title_el:
                continue
            link = title_el.get("href", "")
            if "/RU=" in link:
                try:
                    m = re.search(r"/RU=([^/]+)/", link)
                    if m:
                        link = unquote(m.group(1))
                except Exception:
                    pass
            if not link or not link.startswith("http") or "yahoo.com" in link:
                continue
            items.append({
                "title":       title_el.get_text(strip=True),
                "link":        link,
                "displayLink": _clean_display(link),
                "snippet":     snippet_el.get_text(strip=True) if snippet_el else "",
                "source":      "yahoo",
            })
    except Exception:
        pass
    return items


# ---------------------------------------------------------------------------
# Smart query builder
# ---------------------------------------------------------------------------

def _build_queries(group: dict[str, Any], q: str) -> list[str]:
    """
    Expand operator templates.
    Always uses exact quoted query to enforce precise matching.
    Single-word queries also get an unquoted variant as fallback.
    """
    is_single = len(q.split()) == 1
    queries:  list[str] = []
    seen:     set[str]  = set()

    # Always start with the exact quoted query — guarantees precise results
    exact = f'"{q}"'
    if exact not in seen:
        queries.append(exact)
        seen.add(exact)

    for op in group.get("operators", []):
        # Force quoted version even when operator uses {q} without quotes
        built = op.replace('"{q}"', f'"{q}"').replace("{q}", f'"{q}"')
        if built not in seen:
            queries.append(built)
            seen.add(built)

    # Single-word fallback — unquoted for wider net if exact gives < 5 results
    if is_single:
        unquoted = q
        if unquoted not in seen:
            queries.append(unquoted)
            seen.add(unquoted)

    return queries


# ---------------------------------------------------------------------------
# Group dispatcher — decides which engines to use per group/category
# ---------------------------------------------------------------------------

def _search_group(group: dict[str, Any], q: str) -> tuple[str, list[dict[str, Any]]]:
    queries   = _build_queries(group, q)
    q_words   = [w.lower() for w in q.split() if len(w) >= 2]  # ordered list — preserves word order
    is_strict = group["category"] in ("person", "username", "email", "phone")
    gid       = group["id"]
    all_raw:  list[dict[str, Any]] = []

    # ── Inject open API results per group ───────────────────────────────────
    if gid in ("person_github", "username_dev"):
        try: all_raw.extend(_api_github_search(q))
        except Exception: pass

    if gid in ("person_social", "username_social"):
        try: all_raw.extend(_api_reddit_search(q))
        except Exception: pass

    if gid in ("domain_whois", "domain_certs", "domain_subdomains"):
        try:
            all_raw.extend(_api_crtsh(q))
            all_raw.extend(_api_hackertarget_dns(q))
        except Exception: pass

    if gid in ("domain_archive",):
        try:
            all_raw.extend(_api_wayback(q))
            all_raw.extend(_api_urlscan(q))
        except Exception: pass

    if gid in ("domain_tech",):
        try: all_raw.extend(_api_urlscan(q))
        except Exception: pass

    # ── Electron worker — real browser, Google included ─────────────────────
    # Only fires if the Electron worker server is running (desktop app mode)
    # ── OSINT enrichment scripts — structured data per target type ─────────
    if _OSINT_SCRIPTS_AVAILABLE:
        try:
            cat = group["category"]
            if cat == "phone":
                all_raw.extend(enrich_phone(q))
            elif cat == "domain":
                all_raw.extend(enrich_url(q))
            elif cat == "email":
                all_raw.extend(enrich_email(q))
            elif cat == "username":
                all_raw.extend(enrich_username(q))
            elif cat == "person":
                all_raw.extend(enrich_person(q))
        except Exception:
            pass

    # Worker only for priority groups — avoids flooding Google with all groups
    WORKER_PRIORITY = {
        'person_web', 'person_social', 'person_linkedin', 'person_twitter',
        'person_instagram', 'person_facebook', 'person_news', 'person_github',
        'username_exact', 'username_social', 'username_dev',
        'email_exact', 'email_breach', 'email_social',
        'phone_exact', 'phone_reverse',
        'domain_whois', 'domain_exposed', 'domain_emails',
    }
    if _is_worker_available() and gid in WORKER_PRIORITY:
        worker_q = queries[0] if queries else q
        try:
            results_g = _fetch_electron_worker("google", worker_q)
            all_raw.extend(results_g)
            if len(_deduplicate(all_raw, q_words, is_strict)) < 5:
                results_b = _fetch_electron_worker("bing", worker_q)
                all_raw.extend(results_b)
        except Exception:
            pass
        deduped_early = _deduplicate(all_raw, q_words, is_strict)
        if len(deduped_early) >= MAX_PER_GROUP:
            return gid, deduped_early

    # ── Scraping engines ─────────────────────────────────────────────────────
    for query in queries:
        if len(all_raw) >= MAX_PER_GROUP * 3:
            break

        # Primary: Bing + DDG + Startpage
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            f_bing = ex.submit(_fetch_bing,       query)
            f_ddg  = ex.submit(_fetch_duckduckgo, query)
            f_sp   = ex.submit(_fetch_startpage,  query)
            for f in concurrent.futures.as_completed([f_bing, f_ddg, f_sp], timeout=GROUP_TIMEOUT):
                try:
                    all_raw.extend(f.result() or [])
                except Exception:
                    pass

        # Fallback: Brave + Mojeek + Yahoo if < 5 results
        deduped = _deduplicate(all_raw, q_words, is_strict)
        if len(deduped) < 5:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                f_brave  = ex.submit(_fetch_brave,  query)
                f_mojeek = ex.submit(_fetch_mojeek, query)
                f_yahoo  = ex.submit(_fetch_yahoo,  query)
                for f in concurrent.futures.as_completed([f_brave, f_mojeek, f_yahoo], timeout=GROUP_TIMEOUT):
                    try:
                        all_raw.extend(f.result() or [])
                    except Exception:
                        pass

    return gid, _deduplicate(all_raw, q_words, is_strict)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@method_decorator(xframe_options_exempt, name="dispatch")
class SearchProxyView(View):
    """
    GET /api/search/?q=<query>[&categories=people,files,contact,web]
    Supports SSE streaming via Accept: text/event-stream
    """

    def get(self, request):  # type: ignore[override]
        q = request.GET.get("q", "").strip()
        if not q:
            return JsonResponse({"error": "No query provided"}, status=400)

        raw_cats     = request.GET.get("categories", "").strip()
        allowed_cats: set[str] | None = None
        if raw_cats and raw_cats != "all":
            allowed_cats = {c.strip().lower() for c in raw_cats.split(",") if c.strip()}

        groups = [
            g for g in HACKING_GROUPS
            if allowed_cats is None or g["category"] in allowed_cats
        ]
        if not groups:
            return JsonResponse({"error": "No valid categories specified"}, status=400)

        accept = request.META.get("HTTP_ACCEPT", "")
        if "text/event-stream" in accept:
            return self._stream(q, groups)
        return self._json(q, groups)

    def _json(self, q: str, groups: list[dict[str, Any]]) -> JsonResponse:
        cache_key = _normalise_cache_key(q + "|" + ",".join(g["id"] for g in groups))
        cached    = cache.get(cache_key)
        if cached:
            return JsonResponse({"groups": cached, "cached": True})
        groups_out = self._run_all(q, groups)
        if not groups_out:
            return JsonResponse({"error": "No results found. Try a different query."}, status=503)
        cache.set(cache_key, groups_out, timeout=CACHE_TTL)
        return JsonResponse({"groups": groups_out, "cached": False})

    def _stream(self, q: str, groups: list[dict[str, Any]]) -> StreamingHttpResponse:
        cache_key  = _normalise_cache_key(q + "|" + ",".join(g["id"] for g in groups))
        cached_all = cache.get(cache_key)

        def _sse(payload: dict[str, Any]) -> str:
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        def generate():
            if cached_all:
                for gd in cached_all:
                    yield _sse({"type": "group", "group": gd})
                yield _sse({"type": "done", "cached": True, "total": len(cached_all)})
                return

            collected: list[dict[str, Any]] = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(groups), 16)) as ex:
                fm = {ex.submit(_search_group, g, q): g for g in groups}
                # Use iter + manual timeout to avoid TimeoutError crash in Python 3.14
                deadline = time.time() + 120
                pending  = set(fm.keys())
                done_ids: set[str] = set()
                while pending and time.time() < deadline:
                    finished, pending = concurrent.futures.wait(
                        pending,
                        timeout=min(5, max(0, deadline - time.time())),
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )
                    for future in finished:
                        try:
                            gid, items = future.result()
                        except Exception:
                            continue
                        if not items or gid in done_ids:
                            continue
                        done_ids.add(gid)
                        meta = GROUP_BY_ID.get(gid, {})
                        gd   = {"id": gid, "label": meta.get("label", gid), "items": items}
                        collected.append(gd)
                        yield _sse({"type": "group", "group": gd})

            if collected:
                cache.set(cache_key, collected, timeout=CACHE_TTL)
                yield _sse({"type": "done", "cached": False, "total": len(collected)})
            else:
                yield _sse({"type": "error", "message": "No results found. Try a different query."})

        response = StreamingHttpResponse(generate(), content_type="text/event-stream")
        response["Cache-Control"]     = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    def _run_all(self, q: str, groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: dict[str, list[dict[str, Any]]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(groups), 16)) as ex:
            futures  = {ex.submit(_search_group, g, q): g for g in groups}
            deadline = time.time() + 120
            pending  = set(futures.keys())
            while pending and time.time() < deadline:
                finished, pending = concurrent.futures.wait(
                    pending,
                    timeout=min(5, max(0, deadline - time.time())),
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )
                for future in finished:
                    try:
                        gid, items = future.result()
                        results[gid] = items
                    except Exception:
                        pass
        return [
            {"id": g["id"], "label": g["label"], "items": results.get(g["id"], [])}
            for g in groups if results.get(g["id"])
        ]


@method_decorator(xframe_options_exempt, name="dispatch")
class SearchGroupsView(View):
    """GET /api/search/groups/ — returns all available group definitions."""

    def get(self, request):  # type: ignore[override]
        categories: dict[str, list[dict[str, str]]] = defaultdict(list)
        for g in HACKING_GROUPS:
            categories[g["category"]].append({"id": g["id"], "label": g["label"]})
        return JsonResponse({"categories": dict(categories)})