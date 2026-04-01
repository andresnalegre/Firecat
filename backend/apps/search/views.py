import httpx
import random
import hashlib
import concurrent.futures
import re
from urllib.parse import unquote, parse_qs, urlparse
from bs4 import BeautifulSoup
from django.http import JsonResponse
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
]

HACKING_GROUPS = [
    {'id': 'people_general',    'label': '👤 People — General',      'operator': '{q} person'},
    {'id': 'people_social_all', 'label': '🌐 All Social Media',      'operator': '{q} (site:linkedin.com OR site:twitter.com OR site:x.com OR site:instagram.com OR site:facebook.com OR site:tiktok.com OR site:reddit.com)'},
    {'id': 'people_linkedin',   'label': '💼 LinkedIn',              'operator': '{q} site:linkedin.com'},
    {'id': 'people_twitter',    'label': '🐦 Twitter / X',           'operator': '{q} (site:twitter.com OR site:x.com)'},
    {'id': 'people_instagram',  'label': '📸 Instagram',             'operator': '{q} site:instagram.com'},
    {'id': 'people_facebook',   'label': '👥 Facebook',              'operator': '{q} site:facebook.com'},
    {'id': 'people_github',     'label': '💻 GitHub',                'operator': '{q} site:github.com'},
    {'id': 'people_youtube',    'label': '▶️ YouTube',               'operator': '{q} site:youtube.com'},
    {'id': 'people_tiktok',     'label': '🎵 TikTok',                'operator': '{q} site:tiktok.com'},
    {'id': 'people_reddit',     'label': '🟠 Reddit',                'operator': '{q} site:reddit.com'},
    {'id': 'people_pastebin',   'label': '📋 Pastes & Leaks',        'operator': '{q} (site:pastebin.com OR site:gist.github.com OR site:paste.ee OR site:rentry.co)'},
    {'id': 'people_location',   'label': '📍 Location & Address',    'operator': '{q} (address OR location OR city OR hometown OR "lives in" OR "based in")'},
    {'id': 'people_news',       'label': '📰 News Mentions',         'operator': '{q} (site:reuters.com OR site:bbc.com OR site:theguardian.com OR site:apnews.com OR site:cnn.com OR site:forbes.com)'},
    {'id': 'people_academic',   'label': '🎓 Academic & Research',   'operator': '{q} (site:researchgate.net OR site:academia.edu OR site:arxiv.org OR site:orcid.org)'},
    {'id': 'people_company',    'label': '🏢 Business & Company',    'operator': '{q} (site:crunchbase.com OR site:bloomberg.com OR site:zoominfo.com OR CEO OR founder)'},
    {'id': 'people_images',     'label': '🖼️ Images & Photos',       'operator': '{q} (site:flickr.com OR site:imgur.com OR filetype:jpg OR filetype:png)'},
    {'id': 'contact_email',     'label': '📧 Email Addresses',       'operator': '{q} ("@gmail.com" OR "@yahoo.com" OR "@outlook.com" OR "@hotmail.com" OR "@protonmail.com" OR email)'},
    {'id': 'contact_phone',     'label': '📞 Phone Numbers',         'operator': '{q} (phone OR "tel:" OR telephone OR mobile OR "+1" OR "+44" OR "+55")'},
    {'id': 'contact_address',   'label': '🏠 Physical Address',      'operator': '{q} (address OR street OR avenue OR "zip code" OR "postal code")'},
    {'id': 'contact_whatsapp',  'label': '💬 WhatsApp & Messaging',  'operator': '{q} (whatsapp OR telegram OR signal OR "wa.me" OR "t.me" OR discord)'},
    {'id': 'contact_maps',      'label': '🗺️ Maps & Coordinates',    'operator': '{q} (site:maps.google.com OR site:google.com/maps OR coordinates OR latitude OR longitude)'},
    {'id': 'contact_directory', 'label': '📒 People Directories',    'operator': '{q} (site:whitepages.com OR site:spokeo.com OR site:truepeoplesearch.com OR site:411.com)'},
    {'id': 'contact_records',   'label': '📜 Public Records',        'operator': '{q} ("public record" OR "court record" OR "property record" OR "voter registration")'},
    {'id': 'contact_whois',     'label': '🌐 Domain & WHOIS',        'operator': '{q} (site:whois.domaintools.com OR site:who.is OR whois OR "domain owner")'},
    {'id': 'contact_breach',    'label': '🔓 Data Breaches & Leaks', 'operator': '{q} (site:haveibeenpwned.com OR site:dehashed.com OR "data breach" OR leaked)'},
    {'id': 'contact_osint',     'label': '🕵️ OSINT Aggregators',     'operator': '{q} (site:intelx.io OR site:pipl.com OR site:peekyou.com OR site:beenverified.com)'},
    {'id': 'files_general',     'label': '📁 General Files',         'operator': '"{q}" (filetype:pdf OR filetype:doc OR filetype:xls OR filetype:txt OR filetype:csv)'},
    {'id': 'files_pdf',         'label': '📄 PDF Documents',         'operator': '"{q}" filetype:pdf'},
    {'id': 'files_office',      'label': '📊 Office Documents',      'operator': '"{q}" (filetype:doc OR filetype:docx OR filetype:xls OR filetype:xlsx OR filetype:ppt OR filetype:pptx)'},
    {'id': 'files_text',        'label': '📝 Text & Data Files',     'operator': '"{q}" (filetype:txt OR filetype:csv OR filetype:tsv OR filetype:log)'},
    {'id': 'files_code',        'label': '💾 Code & Scripts',        'operator': '"{q}" (filetype:py OR filetype:js OR filetype:php OR filetype:sh OR filetype:rb OR filetype:java)'},
    {'id': 'files_config',      'label': '⚙️ Config & Env Files',    'operator': '"{q}" (filetype:conf OR filetype:ini OR filetype:cfg OR inurl:".env" OR inurl:"config.php")'},
    {'id': 'files_database',    'label': '🗄️ Database Files',        'operator': '"{q}" (filetype:sql OR filetype:db OR filetype:sqlite OR inurl:phpmyadmin)'},
    {'id': 'files_data',        'label': '🔢 JSON / XML / YAML',     'operator': '"{q}" (filetype:json OR filetype:xml OR filetype:yaml OR filetype:yml)'},
    {'id': 'files_archive',     'label': '🗜️ Archives',              'operator': '"{q}" (filetype:zip OR filetype:tar OR filetype:gz OR filetype:rar OR filetype:7z)'},
    {'id': 'files_backup',      'label': '💿 Backup Files',          'operator': '"{q}" (filetype:bak OR filetype:old OR filetype:backup OR intitle:"index of" inurl:backup)'},
    {'id': 'files_dirs',        'label': '📂 Exposed Directories',   'operator': '"{q}" intitle:"index of"'},
    {'id': 'files_logs',        'label': '🪵 Log Files',             'operator': '"{q}" (filetype:log OR inurl:"/logs/" OR inurl:"/log/")'},
    {'id': 'web_admin',         'label': '🔐 Admin & Login Panels',  'operator': '"{q}" (inurl:admin OR inurl:login OR inurl:wp-admin OR inurl:cpanel OR inurl:dashboard)'},
    {'id': 'web_api',           'label': '🔌 APIs & Endpoints',      'operator': '"{q}" (inurl:"/api/" OR inurl:"/v1/" OR inurl:"/v2/" OR inurl:swagger OR inurl:graphql)'},
    {'id': 'code_repos',        'label': '📦 Code Repositories',     'operator': '{q} (site:github.com OR site:gitlab.com OR site:bitbucket.org OR site:sourceforge.net)'},
]

BLOCKED_DOMAINS = {
    'zhihu.com', 'baidu.com', 'weibo.com', 'qq.com', 'taobao.com',
    'jd.com', '163.com', 'sina.com.cn', 'sohu.com', 'youku.com',
    'bilibili.com', 'csdn.net', 'cnblogs.com', 'jianshu.com',
    'douban.com', '51cto.com', 'oschina.net', 'segmentfault.com',
    'v2ex.com', 'douyin.com', 'weixin.qq.com', 'mp.weixin.qq.com',
    'yahoo.co.jp', 'nicovideo.jp', 'rakuten.co.jp', 'ameblo.jp',
    'hatena.ne.jp', 'naver.com', 'daum.net', 'tistory.com',
    'vk.com', 'yandex.ru', 'mail.ru', 'ok.ru', 'habr.com',
}

NON_LATIN_RE = re.compile(
    r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff\u0900-\u097f]'
)


def _is_english(item):
    link = item.get('link', '')
    try:
        host = urlparse(link).netloc.lower().replace('www.', '')
        for blocked in BLOCKED_DOMAINS:
            if host == blocked or host.endswith('.' + blocked):
                return False
    except Exception:
        pass
    text      = f"{item.get('title', '')} {item.get('snippet', '')}"
    non_latin = len(NON_LATIN_RE.findall(text))
    total     = len([c for c in text if c.strip()])
    if total > 0 and non_latin / total > 0.30:
        return False
    return True


def _is_relevant(item, q_words):
    if not q_words:
        return True
    text = f"{item.get('title','')} {item.get('snippet','')} {item.get('link','')}".lower()
    return any(w in text for w in q_words)


def _clean_display(link):
    try:
        host = urlparse(link).netloc
        return host.replace('www.', '')
    except Exception:
        return link


def _ua():
    return random.choice(USER_AGENTS)


def _fetch_bing(q, pages=5):
    items = []
    cookies = {
        'MUID':     '1',
        '_EDGE_S':  'mkt=en-US&ui=en-US&setmkt=en-US&setlang=en-US',
        '_EDGE_V':  '1',
        'SRCHD':    'AF=NOFORM',
        'SRCHUID':  'V=2',
        'SRCHUSR':  'DOB=20200101',
        'ENSEARCH': 'BENVER=1',
        'MUIDB':    '1',
    }
    try:
        for first in range(1, pages * 10 + 1, 10):
            try:
                r = httpx.get(
                    'https://www.bing.com/search',
                    params={'q': q, 'setlang': 'en-US', 'cc': 'US', 'mkt': 'en-US',
                            'ensearch': '1', 'first': str(first), 'count': '10', 'FORM': 'PERE'},
                    headers={'User-Agent': _ua(), 'Accept': 'text/html,*/*;q=0.8',
                             'Accept-Language': 'en-US,en;q=1.0', 'DNT': '1'},
                    cookies=cookies, timeout=10, follow_redirects=True,
                )
                if r.status_code != 200:
                    break
                soup    = BeautifulSoup(r.text, 'html.parser')
                results = soup.select('li.b_algo')
                if not results:
                    break
                page_items = 0
                for result in results:
                    title_el   = result.select_one('h2 a')
                    snippet_el = result.select_one('.b_caption p') or result.select_one('.b_snippet') or result.select_one('p')
                    cite_el    = result.select_one('cite')
                    if not title_el:
                        continue
                    link = title_el.get('data-href', '') or title_el.get('href', '')
                    if not link or 'bing.com' in link:
                        if cite_el:
                            raw  = cite_el.get_text(strip=True).split(' ›')[0].strip()
                            link = ('https://' + raw) if not raw.startswith('http') else raw
                        else:
                            continue
                    if not link or not link.startswith('http') or 'bing.com' in link:
                        continue
                    items.append({
                        'title':       title_el.get_text(strip=True),
                        'link':        link,
                        'displayLink': _clean_display(link),
                        'snippet':     snippet_el.get_text(strip=True) if snippet_el else '',
                    })
                    page_items += 1
                if page_items == 0:
                    break
            except Exception:
                break
    except Exception:
        pass
    return items


def _fetch_duckduckgo(q):
    items = []
    try:
        r = httpx.get(
            'https://html.duckduckgo.com/html/',
            params={'q': q, 'kl': 'en-us', 'kp': '-1', 'k1': '-1'},
            headers={'User-Agent': _ua(), 'Accept-Language': 'en-US,en;q=1.0',
                     'Referer': 'https://duckduckgo.com/', 'DNT': '1'},
            timeout=12, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, 'html.parser')
        for result in soup.select('.result'):
            title_el   = result.select_one('.result__title a') or result.select_one('a.result__a')
            snippet_el = result.select_one('.result__snippet')
            url_el     = result.select_one('.result__url')
            if not title_el:
                continue
            link = title_el.get('href', '')
            if 'uddg=' in link:
                try:
                    link = unquote(parse_qs(urlparse(link).query).get('uddg', [''])[0])
                except Exception:
                    pass
            if not link or not link.startswith('http'):
                continue
            display = url_el.get_text(strip=True) if url_el else _clean_display(link)
            items.append({
                'title':       title_el.get_text(strip=True),
                'link':        link,
                'displayLink': display.replace('www.', ''),
                'snippet':     snippet_el.get_text(strip=True) if snippet_el else '',
            })
    except Exception:
        pass
    return items


def _fetch_brave(q):
    items = []
    try:
        r = httpx.get(
            'https://search.brave.com/search',
            params={'q': q, 'source': 'web', 'lang': 'en', 'country': 'us'},
            headers={'User-Agent': _ua(), 'Accept-Language': 'en-US,en;q=1.0',
                     'Referer': 'https://search.brave.com/', 'DNT': '1'},
            timeout=12, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, 'html.parser')
        for result in soup.select('[data-type="web"] .snippet, .snippet[data-type], div.snippet'):
            title_el   = result.select_one('.snippet-title') or result.select_one('span.title') or result.select_one('a span')
            snippet_el = result.select_one('.snippet-description') or result.select_one('p.desc') or result.select_one('p')
            link_el    = result.select_one('a[href]')
            if not link_el:
                continue
            link = link_el.get('href', '')
            if not link or not link.startswith('http') or 'brave.com' in link:
                continue
            title = title_el.get_text(strip=True) if title_el else ''
            if not title:
                continue
            items.append({
                'title':       title,
                'link':        link,
                'displayLink': _clean_display(link),
                'snippet':     snippet_el.get_text(strip=True) if snippet_el else '',
            })
    except Exception:
        pass
    return items


def _fetch_mojeek(q):
    items = []
    try:
        r = httpx.get(
            'https://www.mojeek.com/search',
            params={'q': q, 'lang': 'en', 'country': 'US', 'arc': 'none'},
            headers={'User-Agent': _ua(), 'Accept-Language': 'en-US,en;q=1.0',
                     'Referer': 'https://www.mojeek.com/', 'DNT': '1'},
            timeout=10, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, 'html.parser')
        for result in soup.select('ul.results-standard li'):
            title_el   = result.select_one('a.title')
            snippet_el = result.select_one('p.s')
            url_el     = result.select_one('a.ob')
            if not title_el:
                continue
            link = title_el.get('href', '')
            if not link or not link.startswith('http'):
                continue
            items.append({
                'title':       title_el.get_text(strip=True),
                'link':        link,
                'displayLink': url_el.get_text(strip=True).replace('www.', '') if url_el else _clean_display(link),
                'snippet':     snippet_el.get_text(strip=True) if snippet_el else '',
            })
    except Exception:
        pass
    return items


def _fetch_yahoo(q):
    items = []
    try:
        r = httpx.get(
            'https://search.yahoo.com/search',
            params={'p': q, 'ei': 'UTF-8', 'n': '20', 'fl': '1', 'vl': 'lang_en'},
            headers={'User-Agent': _ua(), 'Accept-Language': 'en-US,en;q=1.0',
                     'Referer': 'https://search.yahoo.com/', 'DNT': '1'},
            timeout=10, follow_redirects=True,
        )
        if r.status_code != 200:
            return items
        soup = BeautifulSoup(r.text, 'html.parser')
        for result in soup.select('div.algo, div.Sr'):
            title_el   = result.select_one('h3 a') or result.select_one('h3.title a')
            snippet_el = result.select_one('p') or result.select_one('.compText') or result.select_one('div.s')
            if not title_el:
                continue
            link = title_el.get('href', '')
            if 'yahoo.com/url' in link or '/RU=' in link:
                try:
                    m = re.search(r'/RU=([^/]+)/', link)
                    if m:
                        link = unquote(m.group(1))
                except Exception:
                    pass
            if not link or not link.startswith('http') or 'yahoo.com' in link:
                continue
            items.append({
                'title':       title_el.get_text(strip=True),
                'link':        link,
                'displayLink': _clean_display(link),
                'snippet':     snippet_el.get_text(strip=True) if snippet_el else '',
            })
    except Exception:
        pass
    return items


def _build_query(group, q):
    operator = group['operator']
    if not operator:
        return q
    is_people = (
        group['id'].startswith('people_') or
        group['id'].startswith('contact_') or
        group['id'] == 'code_repos'
    )
    if '"{q}"' in operator:
        return operator.replace('"{q}"', f'"{q}"')
    elif is_people:
        return operator.replace('{q}', f'"{q}"')
    else:
        return operator.replace('{q}', q)


def _search_group(group, q):
    full_q  = _build_query(group, q)
    all_raw = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futures = [
            ex.submit(_fetch_bing,       full_q),
            ex.submit(_fetch_duckduckgo, full_q),
            ex.submit(_fetch_brave,      full_q),
            ex.submit(_fetch_mojeek,     full_q),
            ex.submit(_fetch_yahoo,      full_q),
        ]
        for f in concurrent.futures.as_completed(futures, timeout=20):
            try:
                res = f.result()
                if res:
                    all_raw.extend(res)
            except Exception:
                pass

    is_people_group = (
        group['id'].startswith('people_') or
        group['id'].startswith('contact_') or
        group['id'] == 'code_repos'
    )
    q_words = set(w.lower() for w in q.split() if len(w) >= 2)

    seen  = set()
    final = []
    for item in all_raw:
        url = item.get('link', '')
        if not url or url in seen:
            continue
        if not _is_english(item):
            continue
        if not item.get('title', '').strip():
            continue
        if q_words:
            text = f"{item.get('title','')} {item.get('snippet','')} {url}".lower()
            if is_people_group:
                if not any(w in text for w in q_words):
                    continue
            else:
                matches = sum(1 for w in q_words if w in text)
                if matches < max(1, len(q_words) // 2):
                    continue
        seen.add(url)
        final.append(item)

    return group['id'], final


@method_decorator(xframe_options_exempt, name='dispatch')
class SearchProxyView(View):

    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q:
            return JsonResponse({'error': 'No query provided'}, status=400)

        cache_key = f'deep_{hashlib.md5(q.encode()).hexdigest()}'
        cached    = cache.get(cache_key)
        if cached:
            return JsonResponse({'groups': cached, 'cached': True})

        groups_result = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(HACKING_GROUPS)) as ex:
            futures = {
                ex.submit(_search_group, group, q): group
                for group in HACKING_GROUPS
            }
            for future in concurrent.futures.as_completed(futures, timeout=50):
                try:
                    group_id, items = future.result()
                    groups_result[group_id] = items
                except Exception:
                    pass

        groups_out = []
        for group in HACKING_GROUPS:
            items = groups_result.get(group['id'], [])
            if items:
                groups_out.append({
                    'id':    group['id'],
                    'label': group['label'],
                    'items': items,
                })

        if not groups_out:
            return JsonResponse({'error': 'No results found. Try a different query.'}, status=503)

        cache.set(cache_key, groups_out, timeout=300)
        return JsonResponse({'groups': groups_out})