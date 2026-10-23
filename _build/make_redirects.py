#!/usr/bin/env python3
"""
Turn THIS copy of the site into redirect stubs pointing at a new address.

Only needed if the site moves to a host OTHER than this GitHub Pages repo
(if you just add a CNAME to this repo, GitHub redirects github.io → your
domain automatically and you do not need this). See README.md.

    python3 _build/make_redirects.py https://promptmaster.app

GitHub Pages has no server-side redirects, so every old page becomes a tiny
HTML file with <meta http-equiv="refresh">, a canonical link and a JS
fallback that also keeps #fragments. Run it in a separate checkout/branch of
the OLD repo, commit, push. Old links in released app versions keep working.
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STUB = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PromptMaster has moved</title>
  <meta name="robots" content="noindex">
  <link rel="canonical" href="{url}">
  <meta http-equiv="refresh" content="0; url={url}">
  <script>location.replace({js} + location.pathname + location.search + location.hash);</script>
</head>
<body>
  <p>PromptMaster has moved to <a href="{url}">{url}</a>.</p>
</body>
</html>
"""


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith("https://"):
        sys.exit("usage: make_redirects.py https://new-domain.example")
    new = sys.argv[1].rstrip("/")
    count = 0
    for f in ROOT.rglob("*.html"):
        if "_build" in f.parts or ".git" in f.parts:
            continue
        rel = f.relative_to(ROOT).as_posix()
        if rel == "404.html":
            path = "/"
        elif rel.endswith("index.html"):
            path = "/" + rel[: -len("index.html")]
        else:
            path = "/" + rel
        url = new + path
        f.write_text(STUB.format(url=html.escape(url), js=repr(new)), "utf-8")
        count += 1
    (ROOT / "sitemap.xml").unlink(missing_ok=True)
    (ROOT / "robots.txt").write_text("User-agent: *\nAllow: /\n", "utf-8")
    print(f"Wrote {count} redirect stubs to {new}. Removed sitemap.xml.")


if __name__ == "__main__":
    main()
