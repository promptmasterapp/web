#!/usr/bin/env python3
"""
PromptMaster website generator (optional convenience — the site itself has no
build step: the generated HTML files are committed and served as-is).

    python3 _build/build.py

Reads the texts from _build/i18n/<lang>.json and (re)writes:
  index.html, 404.html, sitemap.xml, robots.txt, app-ads.txt, .nojekyll,
  <lang>/index.html, <lang>/privacy/index.html, <lang>/terms/index.html,
  <lang>/support/index.html

WARNING: running it overwrites those HTML files. If you edited an HTML file by
hand, copy the change into the JSON (or the template below) first.

Standard library only; Python 3.8+.
"""
import html
import json
import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# The ONE place where the public address of the site lives. Only absolute URLs
# (canonical, hreflang, Open Graph, sitemap) use it; every link between pages
# is relative. See README.md → "Moving to a custom domain".
BASE = "https://promptmaster.tikistudios.io"
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
I18N = Path(__file__).resolve().parent / "i18n"
LANGS = ["en", "tr", "de", "fr", "es", "it", "ru", "zh", "ja", "ko"]
DEFAULT = "en"
HREFLANG = {"zh": "zh-Hans"}  # BCP 47 tag used in <html lang> and hreflang
LATIN = {"en", "tr", "de", "fr", "es", "it"}  # Baloo 2 / Figtree cover these
SUPPORT_EMAIL = "support@tikistudios.io"
PUBLISHER = "Tiki Studios"          # developer/operator of the app (legal "we")
BUNDLE_ID = "com.caly.promptmaster"  # iOS bundle ID and Android package name
LAST_MOD = "2026-10-04"
PAGES = ["", "privacy/", "terms/", "support/"]  # per language, relative to /<lang>/
APP_ADS = "google.com, pub-6728738524741574, DIRECT, f08c47fec0942fa0\n"

FONT_LATIN = ("https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800"
              "&family=Figtree:wght@400;500;600;700;800&display=swap")
# Non-Latin pages use the system font (like the app does); only the wordmark
# needs Baloo 2, so Google Fonts sends just those glyphs (a few KB).
FONT_WORDMARK = "https://fonts.googleapis.com/css2?family=Baloo+2:wght@800&text=PromptMaster&display=swap"

T = {}  # lang -> texts


def load():
    for lang in LANGS:
        T[lang] = json.loads((I18N / f"{lang}.json").read_text("utf-8"))


def tag(lang):
    return HREFLANG.get(lang, lang)


def esc(s):
    return html.escape(s, quote=True)


def rel(from_dir, to):
    """Relative URL from the directory of one page (e.g. 'en/privacy/') to a
    target path (e.g. 'en/', 'assets/site.css', 'en/#faq')."""
    frag = ""
    if "#" in to:
        to, frag = to.split("#", 1)
        frag = "#" + frag
    up = "../" * from_dir.count("/")
    out = up + to
    return (out or "./") + frag


# ----------------------------------------------------------------- markup ---
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def inline(s, ctx):
    """Lightweight inline markup: **bold**, [text](url), {support}/{privacy}/{terms}/{home}."""
    for key in ("support", "privacy", "terms", "home"):
        s = s.replace("{" + key + "}", ctx["links"][key])
    s = esc(s)
    s = BOLD_RE.sub(r"<strong>\1</strong>", s)

    def link(m):
        text, url = m.group(1), m.group(2)
        ext = url.startswith("http")
        attrs = ' rel="noopener"' if ext else ""
        return f'<a href="{url}"{attrs}>{text}</a>'

    return LINK_RE.sub(link, s)


def blocks(items, ctx):
    """Block markup: '- ' bullet, '### ' subheading, '! ' callout, else paragraph."""
    out, ul = [], []

    def flush():
        if ul:
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in ul) + "</ul>")
            ul.clear()

    for b in items:
        if b.startswith("- "):
            ul.append(inline(b[2:], ctx))
            continue
        flush()
        if b.startswith("### "):
            out.append(f"<h3>{inline(b[4:], ctx)}</h3>")
        elif b.startswith("! "):
            out.append(f'<div class="callout"><p>{inline(b[2:], ctx)}</p></div>')
        else:
            out.append(f"<p>{inline(b, ctx)}</p>")
    flush()
    return "\n".join(out)


def hero_title(s):
    # Only <em> is allowed in the hero headline.
    s = esc(s).replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
    return s


# ------------------------------------------------------------------ icons ---
def icon(name, cls="ico"):
    p = ICONS[name]
    return (f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{p}</svg>')


ICONS = {
    "flame": '<path fill="currentColor" d="M12.6 2.2c.3 2.6-.7 4.3-2 5.9-1.4 1.7-3.1 3.3-3.1 6.2A4.9 4.9 0 0 0 12 19.2a4.7 4.7 0 0 0 4.8-4.9c0-1.4-.5-2.6-1.3-3.6-.2 1-.8 1.8-1.7 2.2.4-2.8-.2-5.8-1.2-10.7ZM12 22a7.6 7.6 0 0 1-7.8-7.6c0-4 2.2-6.1 3.8-8 .9-1.1 1.6-2 1.8-3.3.1-.8 1-1.2 1.6-.7 3.6 2.8 5.7 5.8 6.3 8.2.4-.4.7-.9.8-1.5.2-.7 1-1 1.6-.5 1.2 1.2 1.7 3.4 1.7 5.6C21.8 18.6 17.6 22 12 22Z"/>',
    "heart": '<path fill="currentColor" d="M12 21s-7.5-4.6-9.6-9.3C.9 8.3 3 4.5 6.6 4.5c2.1 0 3.4 1.1 5.4 3.1 2-2 3.3-3.1 5.4-3.1 3.6 0 5.7 3.8 4.2 7.2C19.5 16.4 12 21 12 21Z"/>',
    "bolt": '<path fill="currentColor" d="M13.5 2 4 13.6h6.6L9.5 22 20 9.6h-6.8L13.5 2Z"/>',
    "gem": '<path fill="currentColor" d="M7 3h10l4.5 6L12 21.5 2.5 9 7 3Zm1 2-2.6 3.5h13.2L16 5H8Z"/>',
    "trophy": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M7 4h10v5a5 5 0 0 1-10 0V4Zm0 2H4v1.5A3.5 3.5 0 0 0 7.5 11M17 6h3v1.5a3.5 3.5 0 0 1-3.5 3.5M12 14v4m-4 3h8l-1-3H9l-1 3Z"/>',
    "book": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15ZM4 20.5A2.5 2.5 0 0 0 6.5 23H20M8 7.5h8"/>',
    "star": '<path fill="currentColor" d="m12 2.8 2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.2l-5.6 3 1.1-6.3L2.9 9.5l6.3-.9L12 2.8Z"/>',
    "check": '<path fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="m5 12.5 4.5 4.5L19 7.5"/>',
    "plus": '<path fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" d="M12 5v14M5 12h14"/>',
    "globe": '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm-8.5-6h17M3.5 9h17M12 3c2.3 2.4 3.4 5.4 3.4 9s-1.1 6.6-3.4 9c-2.3-2.4-3.4-5.4-3.4-9S9.7 5.4 12 3Z"/>',
    "chev": '<path fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="m6 9 6 6 6-6"/>',
    "arrow": '<path fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="M5 12h14m-6-6 6 6-6 6"/>',
    "mail": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M3.5 6.5h17v11h-17v-11Zm0 .5 8.5 6.5L20.5 7"/>',
    "lock": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M6 10.5h12v10H6v-10Zm2.5 0V7.5a3.5 3.5 0 0 1 7 0v3M12 14.5v2"/>',
    "phone": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M8 2.5h8a2 2 0 0 1 2 2v15a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-15a2 2 0 0 1 2-2Zm3 16h2"/>',
    "play": '<path fill="currentColor" d="M6 3.6c0-.8.9-1.3 1.6-.9l12.6 8.4c.6.4.6 1.4 0 1.8L7.6 21.3c-.7.4-1.6 0-1.6-.9V3.6Z"/>',
    "refresh": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M20 11a8 8 0 0 0-14.3-4.9L4 8m0-4v4h4m-4 5a8 8 0 0 0 14.3 4.9L20 16m0 4v-4h-4"/>',
    "bell": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15L6 16Zm4 4.5a2.2 2.2 0 0 0 4 0"/>',
    "shield": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M12 3 4.5 6v5.5c0 4.5 3.2 8.2 7.5 9.5 4.3-1.3 7.5-5 7.5-9.5V6L12 3Zm-3.5 9 2.5 2.5 4.5-5"/>',
    "card": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M3 6h18v12H3V6Zm0 4h18M7 15h4"/>',
    # role icons
    "architect": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M3 21h18M5 21V10l7-5 7 5v11M9.5 21v-6h5v6M9 11h.01M15 11h.01"/>',
    "developer": '<path fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="m8 7-5 5 5 5m8-10 5 5-5 5M13.5 4l-3 16"/>',
    "teacher": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M3 4.5h18v11H3v-11ZM8 20l4-4.5 4 4.5M7 8.5h6m-6 3h9"/>',
    "marketer": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M4 10v4a1 1 0 0 0 1 1h2l6 4.5v-15L7 9H5a1 1 0 0 0-1 1Zm13-1.5a4.5 4.5 0 0 1 0 7M19.5 6a8 8 0 0 1 0 12"/>',
    "student": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="m2.5 9 9.5-4.5L21.5 9 12 13.5 2.5 9Zm4 2v4.5c1.5 1.5 3.5 2.3 5.5 2.3s4-.8 5.5-2.3V11M21.5 9v5.5"/>',
    "curious": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M9 18h6m-5 3h4m-2-18a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3Z"/>',
    "library": '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M4 4h4v16H4V4Zm6 0h4v16h-4V4Zm5.5 1.2 3.8-1 3.7 15.5-3.9.9-3.6-15.4Z"/>',
    "streak": None,
}
ICONS["streak"] = ICONS["flame"]
ICONS["xp"] = ICONS["bolt"]
ICONS["hearts"] = ICONS["heart"]
ICONS["gems"] = ICONS["gem"]
ICONS["league"] = ICONS["trophy"]


# ------------------------------------------------------------------- head ---
def head(lang, page_dir, title, description, alternates, *, noindex=False, og_type="website",
         canonical=True, extra=""):
    t = T[lang]
    css = rel(page_dir, "assets/site.css")
    js = rel(page_dir, "assets/site.js")
    fav = rel(page_dir, "favicon.png")
    ico = rel(page_dir, "favicon.ico")
    apple = rel(page_dir, "apple-touch-icon.png")
    url = f"{BASE}/{page_dir}"
    font = FONT_LATIN if lang in LATIN else FONT_WORDMARK
    alt_links = "\n".join(
        f'  <link rel="alternate" hreflang="{hl}" href="{href}">' for hl, href in alternates)
    og_alt = "\n".join(
        f'  <meta property="og:locale:alternate" content="{T[l]["ogLocale"]}">'
        for l in LANGS if l != lang)
    robots = '  <meta name="robots" content="noindex">\n' if noindex else ""
    canon = f'  <link rel="canonical" href="{url}">\n' if canonical else ""
    return f"""<!doctype html>
<html lang="{tag(lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="author" content="{PUBLISHER}">
{robots}{canon}{alt_links}
  <meta name="theme-color" content="#FFF6EA" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#1C120C" media="(prefers-color-scheme: dark)">
  <meta name="color-scheme" content="light dark">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="PromptMaster">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{BASE}/assets/img/og-image.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="PromptMaster — {esc(t['common']['brandTag'])}">
  <meta property="og:locale" content="{t['ogLocale']}">
{og_alt}
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{ico}" sizes="any">
  <link rel="icon" href="{fav}" type="image/png">
  <link rel="apple-touch-icon" href="{apple}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{font}">
  <link rel="stylesheet" href="{css}">
  <script src="{js}" defer></script>
{extra}</head>
"""


def alternates_for(sub):
    """hreflang list for a per-language page (sub = '', 'privacy/', …)."""
    out = [(tag(l), f"{BASE}/{l}/{sub}") for l in LANGS]
    out.append(("x-default", f"{BASE}/" if sub == "" else f"{BASE}/{DEFAULT}/{sub}"))
    return out


# --------------------------------------------------------- header/footer ---
def lang_switcher(lang, page_dir, sub):
    t = T[lang]
    items = []
    for l in LANGS:
        cur = ' aria-current="page"' if l == lang else ""
        items.append(
            f'<li><a href="{rel(page_dir, l + "/" + sub)}" hreflang="{tag(l)}" lang="{tag(l)}" '
            f'data-lang="{l}"{cur}>{esc(T[l]["name"])}</a></li>')
    return f"""<details class="lang">
        <summary aria-label="{esc(t['common']['language'])}: {esc(t['name'])}">{icon('globe')}<span>{lang.upper()}</span>{icon('chev', 'ico chev')}</summary>
        <ul class="lang-menu">{''.join(items)}</ul>
      </details>"""


def header(lang, page_dir, sub, is_home):
    c = T[lang]["common"]
    home = rel(page_dir, f"{lang}/")
    nav = ""
    if is_home:
        nav = f"""<nav class="nav" aria-label="{esc(T[lang]['name'])}">
        <a href="#how">{esc(c['navHow'])}</a>
        <a href="#paths">{esc(c['navPaths'])}</a>
        <a href="#premium">{esc(c['navPremium'])}</a>
        <a href="#faq">{esc(c['navFaq'])}</a>
      </nav>"""
    else:
        nav = f"""<nav class="nav" aria-label="{esc(T[lang]['name'])}">
        <a href="{rel(page_dir, f'{lang}/support/')}"{' aria-current="page"' if sub == 'support/' else ''}>{esc(c['support'])}</a>
        <a href="{rel(page_dir, f'{lang}/privacy/')}"{' aria-current="page"' if sub == 'privacy/' else ''}>{esc(c['privacy'])}</a>
        <a href="{rel(page_dir, f'{lang}/terms/')}"{' aria-current="page"' if sub == 'terms/' else ''}>{esc(c['terms'])}</a>
      </nav>"""
    get = "#download" if is_home else rel(page_dir, f"{lang}/#download")
    return f"""<a class="skip" href="#main">{esc(c['skip'])}</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{home}" aria-label="{esc(c['logoAlt'])}">
      <img src="{rel(page_dir, 'assets/img/icon-128.webp')}" width="40" height="40" alt="">
      <span class="wordmark">PromptMaster</span>
    </a>
    {nav}
    <div class="header-actions">
      {lang_switcher(lang, page_dir, sub)}
      <a class="btn btn-sm header-cta" href="{get}">{esc(c['getApp'])}</a>
    </div>
  </div>
</header>
"""


def store_badges(lang, cls=""):
    c = T[lang]["common"]
    return f"""<div class="store-badges {cls}">
          <a class="store-badge" href="https://apps.apple.com/us/app/promptmaster-learn-ai-prompts/id6815563992" data-store="ios">{icon('phone', 'ico sb-ico')}<span><small>{esc(c['appStoreSmall'])}</small><b>{esc(c['appStoreBig'])}</b></span></a>
          <a class="store-badge" href="https://play.google.com/store/apps/details?id=com.caly.promptmaster" data-store="android">{icon('play', 'ico sb-ico')}<span><small>{esc(c['playSmall'])}</small><b>{esc(c['playBig'])}</b></span></a>
        </div>"""


def footer(lang, page_dir):
    c = T[lang]["common"]
    L = lambda p: rel(page_dir, f"{lang}/{p}")
    cur = ' aria-current="true"'
    langs = "".join(
        f'<li><a href="{rel(page_dir, l + "/")}" hreflang="{tag(l)}" lang="{tag(l)}" data-lang="{l}"'
        f'{cur if l == lang else ""}>{esc(T[l]["name"])}</a></li>'
        for l in LANGS)
    return f"""<footer class="site-footer">
  <div class="wrap footer-grid">
    <div class="footer-brand">
      <a class="brand" href="{L('')}">
        <img src="{rel(page_dir, 'assets/img/icon-128.webp')}" width="40" height="40" alt="" loading="lazy">
        <span class="wordmark">PromptMaster</span>
      </a>
      <p>{esc(c['footerTagline'])}</p>
      <p><a class="footer-mail" href="mailto:{SUPPORT_EMAIL}">{icon('mail')}{SUPPORT_EMAIL}</a></p>
    </div>
    <nav class="footer-col" aria-label="{esc(c['footerProduct'])}">
      <h2>{esc(c['footerProduct'])}</h2>
      <ul>
        <li><a href="{L('#how')}">{esc(c['navHow'])}</a></li>
        <li><a href="{L('#paths')}">{esc(c['navPaths'])}</a></li>
        <li><a href="{L('#premium')}">{esc(c['navPremium'])}</a></li>
        <li><a href="{L('#faq')}">{esc(c['navFaq'])}</a></li>
      </ul>
    </nav>
    <nav class="footer-col" aria-label="{esc(c['footerLegal'])}">
      <h2>{esc(c['footerLegal'])}</h2>
      <ul>
        <li><a href="{L('privacy/')}">{esc(c['privacy'])}</a></li>
        <li><a href="{L('terms/')}">{esc(c['terms'])}</a></li>
        <li><a href="{L('support/')}">{esc(c['support'])}</a></li>
        <li><a href="mailto:{SUPPORT_EMAIL}">{esc(c['contact'])}</a></li>
      </ul>
    </nav>
    <nav class="footer-col footer-langs" aria-label="{esc(c['language'])}">
      <h2>{esc(c['language'])}</h2>
      <ul>{langs}</ul>
      <p class="all-langs"><a href="{rel(page_dir, '')}?choose">{icon('globe')}{esc(c['allLanguages'])}</a></p>
    </nav>
  </div>
  <div class="wrap footer-bottom">
    <p>{esc(c['rights'])}</p>
  </div>
</footer>
"""


def phone(src, alt, w=560, h=956, eager=False, cls=""):
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<div class="phone {cls}"><img src="{src}" width="{w}" height="{h}" alt="{esc(alt)}" '
            f'{load} decoding="async"></div>')


# -------------------------------------------------------------- home page ---
def page_home(lang):
    t, c, h = T[lang], T[lang]["common"], T[lang]["home"]
    d = f"{lang}/"
    img = lambda n: rel(d, f"assets/img/{n}")
    ctx = {"links": links(lang, d)}

    stats = "".join(
        f'<li><b>{esc(s["n"])}</b><span>{esc(s["l"])}</span></li>' for s in h["stats"])
    steps = "".join(
        f'<li class="step"><span class="step-n" aria-hidden="true">{i + 1}</span>'
        f'<h3>{esc(s["t"])}</h3><p>{esc(s["d"])}</p></li>' for i, s in enumerate(h["steps"]))
    types = "".join(f"<li>{esc(x)}</li>" for x in h["types"])
    crit_vals = [100, 78, 95, 42]
    crit = "".join(
        f'<li><span>{esc(x)}</span><i style="--v:{v}%"></i></li>' for x, v in zip(h["criteria"], crit_vals))
    roles = "".join(
        f'<li class="role role-{r["key"]}"><span class="role-ico">{icon(r["key"])}</span>'
        f'<h3>{esc(r["name"])}</h3><p class="role-hint">{esc(r["hint"])}</p><p>{esc(r["d"])}</p></li>'
        for r in h["roles"])
    game = "".join(
        f'<li class="feat feat-{g["key"]}"><span class="feat-ico">{icon(g["key"])}</span>'
        f'<div><h3>{esc(g["t"])}</h3><p>{esc(g["d"])}</p></div></li>' for g in h["game"])
    ppoints = "".join(f"<li>{icon('check')}<span>{esc(p)}</span></li>" for p in h["privacyPoints"])
    benefits = "".join(f"<li>{icon('check')}<span>{esc(b)}</span></li>" for b in h["premiumBenefits"])
    faq = "".join(
        f'<details class="qa"><summary><span>{esc(q["q"])}</span>{icon("plus", "ico qa-ico")}</summary>'
        f'<div class="qa-body">{blocks([q["a"]], ctx)}</div></details>' for q in h["faq"])

    body = f"""<body class="home">
{header(lang, d, "", True)}
<main id="main">
  <section class="hero">
    <div class="wrap hero-grid">
      <div class="hero-copy">
        <p class="eyebrow">{icon('flame')}{esc(h['heroEyebrow'])}</p>
        <h1>{hero_title(h['heroTitle'])}</h1>
        <p class="lead">{esc(h['heroText'])}</p>
        {store_badges(lang)}
        <p class="hero-note">{icon('check')}{esc(h['heroNote'])}</p>
      </div>
      <div class="hero-visual">
        <div class="blob" aria-hidden="true"></div>
        {phone(img('screen-01.webp'), h['heroShotAlt'], eager=True, cls='phone-hero')}
        <img class="hero-fox" src="{img('fox-hero.webp')}" width="372" height="480" alt="" fetchpriority="high">
        <p class="float-chip chip-streak" aria-hidden="true">{icon('flame')}<b>12</b> {esc(h['chipStreak'])}</p>
        <p class="float-chip chip-xp" aria-hidden="true">{icon('bolt')}<b>+10</b> {esc(h['chipXp'])}</p>
        <p class="float-chip chip-hearts" aria-hidden="true">{icon('heart')}<b>4</b> {esc(h['chipHearts'])}</p>
      </div>
    </div>
  </section>

  <section class="stats-band" aria-label="PromptMaster">
    <div class="wrap"><ul class="stats">{stats}</ul></div>
  </section>

  <section id="how" class="section how" aria-labelledby="how-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{esc(h['howEyebrow'])}</p>
        <h2 id="how-title">{esc(h['howTitle'])}</h2>
        <p class="section-lead">{esc(h['howText'])}</p>
      </div>
      <ol class="steps">{steps}</ol>
      <div class="how-demo">
        <div class="how-phones">
          {phone(img('screen-03.webp'), h['howShot2Alt'], cls='phone-back')}
          {phone(img('screen-04.webp'), h['howShotAlt'], cls='phone-front')}
        </div>
        <div class="how-panel">
          <div class="panel">
            <h3>{esc(h['steps'][1]['t'])}</h3>
            <ul class="type-chips">{types}</ul>
          </div>
          <div class="panel">
            <h3>{esc(h['criteriaLabel'])}</h3>
            <ul class="criteria">{crit}</ul>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section id="paths" class="section paths" aria-labelledby="paths-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{esc(h['pathsEyebrow'])}</p>
        <h2 id="paths-title">{esc(h['pathsTitle'])}</h2>
        <p class="section-lead">{esc(h['pathsText'])}</p>
      </div>
      <ul class="roles">{roles}</ul>
    </div>
  </section>

  <section class="section game" aria-labelledby="game-title">
    <div class="wrap game-grid">
      <div class="game-copy">
        <p class="eyebrow">{esc(h['gameEyebrow'])}</p>
        <h2 id="game-title">{esc(h['gameTitle'])}</h2>
        <p class="section-lead">{esc(h['gameText'])}</p>
        <ul class="feats">{game}</ul>
      </div>
      <div class="game-visual">
        {phone(img('screen-02.webp'), h['gameShot2Alt'], cls='phone-back')}
        {phone(img('screen-05.webp'), h['gameShotAlt'], cls='phone-front')}
        <img class="game-fox" src="{img('fox-master.webp')}" width="254" height="341" alt="" loading="lazy" decoding="async">
      </div>
    </div>
  </section>

  <section class="section privacy-band" aria-labelledby="privacy-title">
    <div class="wrap">
      <div class="privacy-card">
        <div class="privacy-copy">
          <p class="eyebrow">{icon('lock')}{esc(h['privacyEyebrow'])}</p>
          <h2 id="privacy-title">{esc(h['privacyTitle'])}</h2>
          <p>{esc(h['privacyText'])}</p>
          <ul class="checks">{ppoints}</ul>
          <p><a class="text-link" href="privacy/">{esc(h['privacyLink'])}{icon('arrow')}</a></p>
        </div>
        <div class="privacy-visual">
          {phone(img('screen-06.webp'), h['privacyShotAlt'])}
          <img class="privacy-fox" src="{img('fox-sleeping.webp')}" width="348" height="420" alt="" loading="lazy" decoding="async">
        </div>
      </div>
    </div>
  </section>

  <section id="premium" class="section premium" aria-labelledby="premium-title">
    <div class="wrap">
      <div class="premium-card">
        <img class="premium-fox" src="{img('fox-wizard.webp')}" width="254" height="362" alt="" loading="lazy" decoding="async">
        <div class="premium-copy">
          <p class="eyebrow eyebrow-gold">{icon('star')}{esc(h['premiumEyebrow'])}</p>
          <h2 id="premium-title">{esc(h['premiumTitle'])}</h2>
          <p>{esc(h['premiumText'])}</p>
          <ul class="checks checks-gold">{benefits}</ul>
        </div>
        <div class="plans">
          <div class="plan">
            <h3>{esc(h['planMonthly']['t'])}</h3>
            <p>{esc(h['planMonthly']['d'])}</p>
          </div>
          <div class="plan plan-featured">
            <p class="plan-badge">{esc(h['planYearly']['badge'])}</p>
            <h3>{esc(h['planYearly']['t'])}</h3>
            <p>{esc(h['planYearly']['d'])}</p>
          </div>
          <p class="plans-note">{esc(h['premiumNote'])} <a href="terms/#premium">{esc(h['premiumTermsLink'])}</a></p>
        </div>
      </div>
    </div>
  </section>

  <section id="faq" class="section faq" aria-labelledby="faq-title">
    <div class="wrap narrow">
      <div class="section-head">
        <h2 id="faq-title">{esc(h['faqTitle'])}</h2>
      </div>
      <div class="qas">{faq}</div>
    </div>
  </section>

  <section id="download" class="section cta" aria-labelledby="cta-title">
    <div class="wrap">
      <div class="cta-card">
        <img class="cta-fox" src="{img('fox-explorer.webp')}" width="253" height="336" alt="" loading="lazy" decoding="async">
        <div class="cta-copy">
          <h2 id="cta-title">{esc(h['ctaTitle'])}</h2>
          <p>{esc(h['ctaText'])}</p>
          {store_badges(lang, 'on-orange')}
        </div>
      </div>
    </div>
  </section>
</main>
{footer(lang, d)}
</body>
</html>
"""
    ld = {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "name": "PromptMaster: Learn AI Prompts",
        "alternateName": "PromptMaster",
        "description": h["description"],
        "operatingSystem": "iOS, Android",
        "applicationCategory": "EducationalApplication",
        "inLanguage": tag(lang),
        "url": f"{BASE}/{lang}/",
        "image": f"{BASE}/assets/img/icon-512.png",
        "author": {"@type": "Organization", "name": PUBLISHER, "email": SUPPORT_EMAIL},
        "publisher": {"@type": "Organization", "name": PUBLISHER, "email": SUPPORT_EMAIL},
    }
    extra = ('  <script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
             + "</script>\n")
    return head(lang, d, h["title"], h["description"], alternates_for(""), extra=extra) + body


def links(lang, page_dir):
    return {
        "support": rel(page_dir, f"{lang}/support/"),
        "privacy": rel(page_dir, f"{lang}/privacy/"),
        "terms": rel(page_dir, f"{lang}/terms/"),
        "home": rel(page_dir, f"{lang}/"),
    }


# ------------------------------------------------------------ legal pages ---
def page_legal(lang, kind):
    t, c, p = T[lang], T[lang]["common"], T[lang][kind]
    d = f"{lang}/{kind}/"
    ctx = {"links": links(lang, d)}
    toc_items = "".join(f'<li><a href="#{s["id"]}">{esc(s["title"])}</a></li>' for s in p["sections"])
    secs = []
    for i, s in enumerate(p["sections"], 1):
        todo = f"\n      <!-- {s['todo']} -->" if s.get("todo") else ""
        secs.append(f"""{todo}
      <section id="{s['id']}" aria-labelledby="{s['id']}-h">
        <h2 id="{s['id']}-h"><span class="sec-n" aria-hidden="true">{i}</span>{esc(s['title'])}</h2>
        {blocks(s['body'], ctx)}
      </section>""")
    review = "\n<!-- TODO legal review: have this document reviewed by a lawyer before publishing. -->" if kind == "terms" else ""
    fox = "fox-scholar.webp"
    body = f"""<body class="legal">{review}
{header(lang, d, kind + '/', False)}
<main id="main">
  <div class="page-head">
    <div class="wrap page-head-inner">
      <div>
        <p class="crumbs"><a href="../">{esc(c['home'])}</a> <span aria-hidden="true">/</span> <span>{esc(p['h1'])}</span></p>
        <h1>{esc(p['h1'])}</h1>
        <p class="updated"><time datetime="{LAST_MOD}">{esc(c['lastUpdated'])}</time></p>
      </div>
      <img class="page-fox" src="{rel(d, 'assets/img/' + fox)}" width="255" height="336" alt="" decoding="async">
    </div>
  </div>
  <div class="wrap legal-grid">
    <nav class="toc toc-side" aria-label="{esc(c['toc'])}">
      <p class="toc-title">{esc(c['toc'])}</p>
      <ol>{toc_items}</ol>
    </nav>
    <article class="prose">
      <details class="toc toc-inline">
        <summary>{esc(c['toc'])}{icon('chev', 'ico chev')}</summary>
        <ol>{toc_items}</ol>
      </details>
      <div class="intro">{blocks(p['intro'], ctx)}</div>
{''.join(secs)}
      <p class="to-top"><a href="#main">{esc(c['backToTop'])} ↑</a></p>
    </article>
  </div>
</main>
{footer(lang, d)}
</body>
</html>
"""
    return head(lang, d, p["title"], p["description"], alternates_for(kind + "/"), og_type="article") + body


# ----------------------------------------------------------- support page ---
SUPPORT_ICONS = {"subscription": "card", "progress": "refresh", "privacy-ads": "shield", "reminders": "bell"}


def page_support(lang):
    t, c, s = T[lang], T[lang]["common"], T[lang]["support"]
    d = f"{lang}/support/"
    ctx = {"links": links(lang, d)}
    quick = "".join(
        f'<li><a href="#{sec["id"]}">{icon(SUPPORT_ICONS.get(sec["id"], "star"))}<span>{esc(sec["title"])}</span></a></li>'
        for sec in s["sections"])
    groups = []
    for sec in s["sections"]:
        qas = "".join(
            f'<details class="qa" id="{it["id"]}"><summary><span>{esc(it["q"])}</span>{icon("plus", "ico qa-ico")}</summary>'
            f'<div class="qa-body">{blocks(it["a"], ctx)}</div></details>' for it in sec["items"])
        groups.append(f"""
      <section id="{sec['id']}" class="support-group" aria-labelledby="{sec['id']}-h">
        <h2 id="{sec['id']}-h"><span class="sg-ico">{icon(SUPPORT_ICONS.get(sec['id'], 'star'))}</span>{esc(sec['title'])}</h2>
        <div class="qas">{qas}</div>
      </section>""")
    body = f"""<body class="support">
{header(lang, d, 'support/', False)}
<main id="main">
  <div class="page-head">
    <div class="wrap page-head-inner">
      <div>
        <p class="crumbs"><a href="../">{esc(c['home'])}</a> <span aria-hidden="true">/</span> <span>{esc(c['support'])}</span></p>
        <h1>{esc(s['h1'])}</h1>
        <p class="page-lead">{esc(s['intro'])}</p>
        <ul class="quick">{quick}</ul>
      </div>
      <img class="page-fox" src="{rel(d, 'assets/img/fox-surprised.webp')}" width="406" height="480" alt="" decoding="async">
    </div>
  </div>
  <div class="wrap narrow support-body">
{''.join(groups)}
      <section class="contact-card" aria-labelledby="contact-h">
        <span class="contact-ico">{icon('mail')}</span>
        <div>
          <h2 id="contact-h">{esc(s['contactTitle'])}</h2>
          <p>{esc(s['contactText'])}</p>
        </div>
        <a class="btn" href="mailto:{SUPPORT_EMAIL}">{esc(s['emailCta'])}</a>
      </section>
  </div>
</main>
{footer(lang, d)}
</body>
</html>
"""
    return head(lang, d, s["title"], s["description"], alternates_for("support/")) + body


# ------------------------------------------------------------------- root ---
def page_root():
    lang = DEFAULT
    c = T[lang]
    items = "".join(
        f'<li><a href="{l}/" hreflang="{tag(l)}" lang="{tag(l)}" data-lang="{l}">'
        f'<span class="lc">{l.upper()}</span><span class="ln">{esc(T[l]["name"])}</span>'
        f'<span class="lp">{esc(T[l]["chooser"]["tagline"])}</span></a></li>' for l in LANGS)
    redirect = """  <script>
  /* Send first-time visitors to the best language once; a language picked on
     the site (saved in localStorage) wins. ?choose shows this page instead. */
  (function () {
    var L = %s;
    if (/[?&]choose/.test(location.search)) return;
    var saved = null;
    try { saved = localStorage.getItem('pm-lang'); } catch (e) {}
    var target = L.indexOf(saved) > -1 ? saved : null;
    if (!target) {
      try { if (sessionStorage.getItem('pm-redirected')) return; sessionStorage.setItem('pm-redirected', '1'); } catch (e) {}
      var prefs = navigator.languages || [navigator.language || ''];
      for (var i = 0; i < prefs.length && !target; i++) {
        var p = String(prefs[i] || '').toLowerCase().split('-')[0];
        if (L.indexOf(p) > -1) target = p;
      }
      target = target || 'en';
    }
    location.replace(target + '/' + location.hash);
  })();
  </script>
""" % json.dumps(LANGS)
    alts = [(tag(l), f"{BASE}/{l}/") for l in LANGS] + [("x-default", f"{BASE}/")]
    hd = head(lang, "", "PromptMaster: Learn AI Prompts", c["home"]["description"], alts, extra=redirect)
    # the chooser shows every language name → load the Latin fonts
    body = f"""<body class="chooser">
<main id="main" class="chooser-main">
  <div class="chooser-card">
    <img class="chooser-fox" src="assets/img/fox-hero.webp" width="372" height="480" alt="">
    <p class="brand brand-lg"><img src="assets/img/icon-128.webp" width="56" height="56" alt=""><span class="wordmark">PromptMaster</span></p>
    <h1>{esc(c['chooser']['pick'])}</h1>
    <ul class="chooser-list">{items}</ul>
    <p class="chooser-foot"><a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
  </div>
</main>
</body>
</html>
"""
    return hd + body


# -------------------------------------------------------------------- 404 ---
def page_404():
    lang = DEFAULT
    nf = {l: T[l]["notFound"] for l in LANGS}
    links_html = "".join(
        f'<li><a href="/{l}/" hreflang="{tag(l)}" lang="{tag(l)}">{esc(T[l]["name"])}</a></li>' for l in LANGS)
    data = json.dumps({l: {"h1": nf[l]["h1"], "text": nf[l]["text"], "cta": nf[l]["cta"], "title": nf[l]["title"],
                           "tag": tag(l)} for l in LANGS}, ensure_ascii=False)
    alts = [(tag(l), f"{BASE}/{l}/") for l in LANGS] + [("x-default", f"{BASE}/")]
    # 404 can be served at any depth → root-absolute links (same on a custom domain).
    hd = head(lang, "", nf[lang]["title"], nf[lang]["text"], alts, noindex=True, canonical=False)
    hd = hd.replace('href="favicon.ico"', 'href="/favicon.ico"').replace('href="favicon.png"', 'href="/favicon.png"') \
        .replace('href="apple-touch-icon.png"', 'href="/apple-touch-icon.png"') \
        .replace('href="assets/site.css"', 'href="/assets/site.css"').replace('src="assets/site.js"', 'src="/assets/site.js"')
    body = f"""<body class="notfound">
<main id="main" class="chooser-main">
  <div class="chooser-card">
    <img class="nf-fox" src="/assets/img/fox-surprised.webp" width="406" height="480" alt="">
    <p class="nf-code" aria-hidden="true">404</p>
    <h1 id="nf-h1">{esc(nf[lang]['h1'])}</h1>
    <p id="nf-text">{esc(nf[lang]['text'])}</p>
    <p><a id="nf-cta" class="btn" href="/">{esc(nf[lang]['cta'])}</a></p>
    <ul class="nf-langs">{links_html}</ul>
  </div>
</main>
<script>
  /* Show the message in the language of the missing URL (/de/… → German). */
  (function () {{
    var T = {data};
    var m = location.pathname.match(/^\\/([a-z]{{2}})(\\/|$)/);
    var l = m && T[m[1]] ? m[1] : null;
    if (!l) return;
    document.documentElement.lang = T[l].tag;
    document.title = T[l].title;
    document.getElementById('nf-h1').textContent = T[l].h1;
    document.getElementById('nf-text').textContent = T[l].text;
    var a = document.getElementById('nf-cta');
    a.textContent = T[l].cta; a.href = '/' + l + '/';
  }})();
</script>
</body>
</html>
"""
    return hd + body


# ------------------------------------------------------------ misc files ---
def sitemap():
    rows = []
    for sub in PAGES:
        for l in LANGS:
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{hl}" href="{href}"/>'
                for hl, href in alternates_for(sub))
            rows.append(f"""  <url>
    <loc>{BASE}/{l}/{sub}</loc>
    <lastmod>{LAST_MOD}</lastmod>{alts}
  </url>""")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            f"  <url>\n    <loc>{BASE}/</loc>\n    <lastmod>{LAST_MOD}</lastmod>\n  </url>\n"
            + "\n".join(rows) + "\n</urlset>\n")


def robots():
    return f"User-agent: *\nAllow: /\nDisallow: /_build/\n\nSitemap: {BASE}/sitemap.xml\n"


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, "utf-8")


def main():
    load()
    for lang in LANGS:
        write(f"{lang}/index.html", page_home(lang))
        write(f"{lang}/privacy/index.html", page_legal(lang, "privacy"))
        write(f"{lang}/terms/index.html", page_legal(lang, "terms"))
        write(f"{lang}/support/index.html", page_support(lang))
    write("index.html", page_root())
    write("404.html", page_404())
    write("sitemap.xml", sitemap())
    write("robots.txt", robots())
    write("app-ads.txt", APP_ADS)
    write(".nojekyll", "")
    print(f"Built {len(LANGS) * len(PAGES) + 2} pages for {len(LANGS)} languages.")


if __name__ == "__main__":
    main()
