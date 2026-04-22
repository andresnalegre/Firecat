"""
osint_username.py — Active username intelligence
Fetches real GitHub data, checks platform availability, breach exposure.
"""
import re
import httpx
from typing import Any

TIMEOUT = 6
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
GH = {**H, "Accept": "application/vnd.github.v3+json"}


def _r(title, link, snippet, source):
    return {"title": title, "link": link, "snippet": snippet,
            "source": source, "osint": True,
            "displayLink": re.sub(r"https?://", "", link).split("/")[0]}

def _clean(q):
    return re.sub(r'^@', '', q.strip())


def _github(username):
    results = []
    try:
        r = httpx.get(f"https://api.github.com/users/{username}", timeout=TIMEOUT, headers=GH)
        if r.status_code == 200:
            d = r.json()
            results.append(_r(
                f"GitHub — {d.get('name') or username} (@{username})",
                d.get("html_url", f"https://github.com/{username}"),
                f"Name: {d.get('name','?')} · "
                f"Bio: {(d.get('bio') or '—')[:80]} · "
                f"Repos: {d.get('public_repos',0)} · "
                f"Followers: {d.get('followers',0)} · "
                f"Following: {d.get('following',0)} · "
                f"Location: {d.get('location') or '?'} · "
                f"Company: {d.get('company') or '?'} · "
                f"Blog: {d.get('blog') or '?'} · "
                f"Created: {(d.get('created_at',''))[:10]}",
                "github"
            ))
            # Repos
            r2 = httpx.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=6",
                           timeout=TIMEOUT, headers=GH)
            if r2.status_code == 200:
                for repo in r2.json()[:6]:
                    results.append(_r(
                        f"GitHub Repo — {repo.get('full_name','')}",
                        repo.get("html_url", ""),
                        f"{repo.get('description') or 'No description'} · "
                        f"★ {repo.get('stargazers_count',0)} · "
                        f"Forks: {repo.get('forks_count',0)} · "
                        f"Language: {repo.get('language') or '?'} · "
                        f"Updated: {(repo.get('updated_at',''))[:10]}",
                        "github"
                    ))
    except Exception:
        pass
    return results


def _reddit(username):
    results = []
    try:
        r = httpx.get(f"https://www.reddit.com/user/{username}/about.json",
                      timeout=TIMEOUT, headers={**H, "Accept": "application/json"})
        if r.status_code == 200:
            d = r.json().get("data", {})
            results.append(_r(
                f"Reddit — u/{username}",
                f"https://www.reddit.com/user/{username}/",
                f"Karma: {d.get('total_karma',0)} (link: {d.get('link_karma',0)}, "
                f"comment: {d.get('comment_karma',0)}) · "
                f"Created: {__import__('datetime').datetime.fromtimestamp(d.get('created_utc',0)).strftime('%Y-%m-%d')} · "
                f"Verified: {d.get('verified', False)} · "
                f"NSFW: {d.get('over_18', False)}",
                "reddit"
            ))
    except Exception:
        pass
    return results


def _check_platforms(username):
    """Quick HTTP HEAD check on key platforms — 200/301 = exists."""
    platforms = [
        ("Twitter/X",   f"https://twitter.com/{username}"),
        ("Instagram",   f"https://www.instagram.com/{username}/"),
        ("TikTok",      f"https://www.tiktok.com/@{username}"),
        ("YouTube",     f"https://www.youtube.com/@{username}"),
        ("Twitch",      f"https://www.twitch.tv/{username}"),
        ("Medium",      f"https://medium.com/@{username}"),
        ("Dev.to",      f"https://dev.to/{username}"),
        ("GitLab",      f"https://gitlab.com/{username}"),
        ("Codepen",     f"https://codepen.io/{username}"),
        ("Behance",     f"https://www.behance.net/{username}"),
        ("Dribbble",    f"https://dribbble.com/{username}"),
        ("SoundCloud",  f"https://soundcloud.com/{username}"),
        ("Patreon",     f"https://www.patreon.com/{username}"),
        ("Steam",       f"https://steamcommunity.com/id/{username}"),
    ]
    results = []
    for name, url in platforms:
        try:
            r = httpx.head(url, timeout=3, follow_redirects=True,
                           headers={"User-Agent": "Mozilla/5.0"})
            exists = r.status_code in (200, 301, 302)
            if exists:
                results.append(_r(
                    f"{name} — @{username} [FOUND]",
                    url,
                    f"Profile @{username} exists on {name}. Status: {r.status_code}.",
                    name.lower().replace("/", "_")
                ))
        except Exception:
            pass
    return results


def _breach_exposure(username):
    return [
        _r(f"WhatsMyName — @{username}",
           f"https://whatsmyname.app/?q={username}",
           f"Multi-platform username checker for @{username}: scans 500+ sites automatically.",
           "whatsmyname"),
        _r(f"IntelX — @{username}",
           f"https://intelx.io/?s={username}",
           f"Search @{username} across dark web, paste sites and data breaches.",
           "intelx"),
        _r(f"Pastebin — @{username}",
           f"https://pastebin.com/search?q={username}",
           f"Search Pastebin for pastes mentioning @{username}: credentials, config dumps.",
           "pastebin"),
    ]


def enrich_username(q: str) -> list[dict[str, Any]]:
    username = _clean(q)
    out = []
    out.extend(_github(username))
    out.extend(_reddit(username))
    out.extend(_check_platforms(username))
    out.extend(_breach_exposure(username))
    return out