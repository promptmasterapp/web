#!/usr/bin/env python3
"""Check that every translation has exactly the same structure as en.json.

Usage:  python3 _build/check_i18n.py            # all languages
        python3 _build/check_i18n.py de fr      # only some

Checks: same keys, same list lengths, identical ids/keys, same block markers
("- ", "### ", "! "), same {placeholders}, same link targets (except the
language parameter of Apple/Google help links), no leftover English in
structural fields, and that "PromptMaster" and support@tikistudios.io survive.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent / "i18n"
LANGS = ["en", "tr", "de", "fr", "es", "it", "ru", "zh", "ja", "ko"]
FIXED_KEYS = {"id", "key", "todo"}  # must match en exactly
LINK = re.compile(r"\]\(([^)]+)\)")
PH = re.compile(r"\{[a-z]+\}")


def norm_url(u: str) -> str:
    u = re.sub(r"support\.apple\.com/[a-z]{2}-[a-z]{2}/", "support.apple.com/LL/", u)
    u = re.sub(r"([?&])hl=[A-Za-z-]+", r"\1hl=LL", u)
    return u


def marker(s: str) -> str:
    for m in ("- ", "### ", "! "):
        if s.startswith(m):
            return m
    return ""


def walk(en, tr, path, errs):
    if isinstance(en, dict):
        if not isinstance(tr, dict):
            errs.append(f"{path}: expected object")
            return
        for k in en:
            if k not in tr:
                errs.append(f"{path}.{k}: missing")
        for k in tr:
            if k not in en:
                errs.append(f"{path}.{k}: unexpected key")
        for k in en:
            if k in tr:
                walk(en[k], tr[k], f"{path}.{k}", errs)
    elif isinstance(en, list):
        if not isinstance(tr, list) or len(en) != len(tr):
            errs.append(f"{path}: list length {len(tr) if isinstance(tr, list) else '?'} != {len(en)}")
            return
        for i, (a, b) in enumerate(zip(en, tr)):
            walk(a, b, f"{path}[{i}]", errs)
    elif isinstance(en, str):
        if not isinstance(tr, str):
            errs.append(f"{path}: expected string")
            return
        key = path.rsplit(".", 1)[-1]
        if key in FIXED_KEYS and en != tr:
            errs.append(f"{path}: must stay {en!r}")
        if marker(en) != marker(tr):
            errs.append(f"{path}: block marker {marker(tr)!r} != {marker(en)!r}")
        if sorted(PH.findall(en)) != sorted(PH.findall(tr)):
            errs.append(f"{path}: placeholders differ")
        if [norm_url(u) for u in LINK.findall(en)] != [norm_url(u) for u in LINK.findall(tr)]:
            errs.append(f"{path}: links differ: {LINK.findall(tr)}")
        if en.count("**") != tr.count("**"):
            errs.append(f"{path}: bold markers (**) differ")
        if tr.count("**") % 2:
            errs.append(f"{path}: odd number of ** markers")
        for must in ("PromptMaster", "Tiki Studios", "support@tikistudios.io", "<em>"):
            if must in en and must not in tr:
                errs.append(f"{path}: lost {must!r}")
        if "</em>" in en and "</em>" not in tr:
            errs.append(f"{path}: lost </em>")


def main():
    langs = sys.argv[1:] or LANGS
    en = json.loads((HERE / "en.json").read_text("utf-8"))
    bad = 0
    for lang in langs:
        f = HERE / f"{lang}.json"
        if not f.exists():
            print(f"{lang}: MISSING FILE")
            bad += 1
            continue
        try:
            tr = json.loads(f.read_text("utf-8"))
        except json.JSONDecodeError as e:
            print(f"{lang}: INVALID JSON: {e}")
            bad += 1
            continue
        errs = []
        walk(en, tr, lang, errs)
        if tr.get("code") != lang:
            errs.append(f"{lang}.code must be {lang!r}")
        print(f"{lang}: {'OK' if not errs else str(len(errs)) + ' problem(s)'}")
        for e in errs[:60]:
            print("   ", e)
        bad += bool(errs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
