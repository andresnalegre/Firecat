import httpx
import random
import ssl
from bs4 import BeautifulSoup
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
]

STRIP_HEADERS = {
    'x-frame-options',
    'content-security-policy',
    'cross-origin-embedder-policy',
    'cross-origin-opener-policy',
    'cross-origin-resource-policy',
    'transfer-encoding',
    'content-encoding',
    'content-length',
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailers',
    'upgrade',
}

def make_ssl_context():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1
    except Exception:
        pass
    return ctx

@method_decorator(xframe_options_exempt, name='dispatch')
class WebProxyView(View):

    def get(self, request):
        url = request.GET.get('url', '').strip()
        if not url:
            return HttpResponseBadRequest('No URL provided')

        headers = {
            'User-Agent':      random.choice(USER_AGENTS),
            'Accept':          'text/html,application/xhtml+xml,*/*;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
        }

        attempts = [
            lambda: httpx.get(url, headers=headers, timeout=15, follow_redirects=True, verify=False),
            lambda: httpx.get(url, headers=headers, timeout=15, follow_redirects=True,
                              transport=httpx.HTTPSTransport(ssl_context=make_ssl_context())),
            lambda: httpx.get(
                url.replace('https://', 'http://'),
                headers=headers, timeout=15, follow_redirects=True, verify=False
            ),
        ]

        r        = None
        last_err = None
        for attempt in attempts:
            try:
                r = attempt()
                if r.status_code < 500:
                    break
                r = None
            except Exception as e:
                last_err = e
                r = None
                continue

        if r is None:
            return HttpResponse(
                f'<html><body style="font-family:sans-serif;padding:40px;color:#666">'
                f'<h3>Could not load page</h3><p>{str(last_err)}</p></body></html>',
                content_type='text/html', status=502,
            )

        content_type = r.headers.get('content-type', 'text/html')

        if 'text/html' in content_type:
            try:
                soup = BeautifulSoup(r.content, 'html.parser')
                if not soup.find('base'):
                    base = soup.new_tag('base', href=str(r.url))
                    if soup.head:
                        soup.head.insert(0, base)
                    elif soup.html:
                        head = soup.new_tag('head')
                        head.append(base)
                        soup.html.insert(0, head)
                content = str(soup).encode('utf-8')
            except Exception:
                content = r.content
            content_type = 'text/html; charset=utf-8'
        else:
            content = r.content

        response = HttpResponse(content, content_type=content_type, status=r.status_code)

        for key, val in r.headers.items():
            if key.lower() not in STRIP_HEADERS:
                try:
                    response[key] = val
                except Exception:
                    pass

        return response