#!/usr/bin/env python3
"""Crawl the built site locally and check it.

    python3 _build/verify.py

- every internal href/src resolves to a file (directories → index.html), #fragments exist
- HTML structure: balanced tags, one <h1>, unique ids, <html lang>, <title>,
  meta description, canonical (except 404), og tags, alt on every <img>
- hreflang alternates for all languages + x-default on every page
- sitemap URLs map to existing files; app-ads.txt content
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://promptmaster.tikistudios.io"
LANGS = ["en", "tr", "de", "fr", "es", "it", "ru", "zh", "ja", "ko"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
errors = []


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.ids, self.links, self.imgs = [], [], [], []
        self.h1 = 0
        self.lang = None
        self.meta = {}
        self.alternates = []
        self.canonical = None
        self.title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.title = True
        if tag == "img":
            self.imgs.append(a)
        if tag == "meta":
            k = a.get("name") or a.get("property")
            if k:
                self.meta[k] = a.get("content")
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alternates.append((a["hreflang"], a["href"]))
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        for attr in ("href", "src"):
            if attr in a and not (tag == "link" and a.get("rel") in ("alternate", "canonical")):
                self.links.append((tag, a[attr]))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            errors.append(f"{self.file}: unexpected </{tag}> at {self.getpos()} (open: {self.stack[-1] if self.stack else None})")
            # try to recover
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break
            return
        self.stack.pop()


def resolve(page_file: Path, url: str):
    """Return (file path, fragment) for an internal URL, or None for external."""
    if re.match(r"^(https?:|mailto:|tel:|data:)", url) or url.startswith("//"):
        return None
    parts = urlsplit(url)
    path = unquote(parts.path)
    if path.startswith("/"):
        target = ROOT / path.lstrip("/")
    elif path == "":
        target = page_file
    else:
        target = (page_file.parent / path)
    if path.endswith("/") or (target.exists() and target.is_dir()):
        target = target / "index.html"
    return target.resolve(), parts.fragment


def main():
    pages = sorted(p for p in ROOT.rglob("*.html") if "_build" not in p.parts and ".git" not in p.parts)
    parsed = {}
    for f in pages:
        p = Page()
        p.file = f.relative_to(ROOT)
        p.feed(f.read_text("utf-8"))
        p.close()
        parsed[f.resolve()] = p
    n_links = 0
    for f, p in parsed.items():
        rel = f.relative_to(ROOT)
        if p.stack:
            errors.append(f"{rel}: unclosed tags {p.stack[:3]}")
        if p.h1 != 1:
            errors.append(f"{rel}: {p.h1} <h1> elements")
        dup = {i for i in p.ids if p.ids.count(i) > 1}
        if dup:
            errors.append(f"{rel}: duplicate ids {dup}")
        if not p.lang:
            errors.append(f"{rel}: missing <html lang>")
        if not p.title:
            errors.append(f"{rel}: missing <title>")
        for k in ("description", "og:title", "og:description", "og:image", "og:url"):
            if not p.meta.get(k):
                errors.append(f"{rel}: missing meta {k}")
        if rel.name != "404.html" and not (p.canonical or "").startswith(BASE):
            errors.append(f"{rel}: missing canonical")
        hl = {h for h, _ in p.alternates}
        want = {("zh-Hans" if l == "zh" else l) for l in LANGS} | {"x-default"}
        if hl != want:
            errors.append(f"{rel}: hreflang set {sorted(hl)}")
        for h, href in p.alternates + ([("canonical", p.canonical)] if p.canonical else []):
            if not href.startswith(BASE + "/"):
                errors.append(f"{rel}: absolute URL not on BASE: {href}")
                continue
            local = ROOT / href[len(BASE) + 1:]
            if href.endswith("/"):
                local = local / "index.html"
            if not local.exists():
                errors.append(f"{rel}: {h} → {href} has no file")
        for img in p.imgs:
            if "alt" not in img:
                errors.append(f"{rel}: <img src={img.get('src')}> without alt")
            if "width" not in img or "height" not in img:
                errors.append(f"{rel}: <img src={img.get('src')}> without width/height")
        for tag, url in p.links:
            r = resolve(f, url)
            if r is None:
                continue
            n_links += 1
            target, frag = r
            if not target.exists():
                errors.append(f"{rel}: broken {tag} → {url}")
                continue
            if frag and target.suffix == ".html":
                tp = parsed.get(target)
                if tp and frag not in tp.ids:
                    errors.append(f"{rel}: missing anchor #{frag} in {target.relative_to(ROOT)}")
    # per-language page matrix
    for l in LANGS:
        for sub in ("", "privacy/", "terms/", "support/"):
            if not (ROOT / l / sub / "index.html").exists():
                errors.append(f"missing page /{l}/{sub}")
    # sitemap
    sm = (ROOT / "sitemap.xml").read_text("utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    for u in locs:
        local = ROOT / u[len(BASE) + 1:]
        if u.endswith("/"):
            local = local / "index.html"
        if not local.exists():
            errors.append(f"sitemap: {u} has no file")
    if (ROOT / "app-ads.txt").read_text() != "google.com, pub-6728738524741574, DIRECT, f08c47fec0942fa0\n":
        errors.append("app-ads.txt content differs")
    for must in (".nojekyll", "robots.txt", "404.html", "favicon.ico"):
        if not (ROOT / must).exists():
            errors.append(f"missing {must}")
    print(f"{len(parsed)} HTML pages, {n_links} internal links/srcs checked, {len(locs)} sitemap URLs")
    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
