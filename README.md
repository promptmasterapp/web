# PromptMaster website

The public website of the **PromptMaster: Learn AI Prompts** app: product page,
Privacy Policy, Terms of Use and Support in 10 languages, plus `app-ads.txt` for
AdMob.

- Live address: **https://promptmaster.tikistudios.io** (marketing copy of the site; the legal pages and `app-ads.txt` that the shipped app and AdMob use stay on https://promptmasterapp.github.io)
- Repository: `promptmasterapp/promptmasterapp.github.io`, GitHub Pages
  serves the repository root of the default branch.
- Plain static HTML/CSS with one tiny script. There are no frameworks and no
  build step on GitHub: the files in this repo are exactly what is served.

## How the site is organised

```
/
├── index.html            language chooser; sends first-time visitors to their language
├── 404.html              "page not found" (shows its text in the language of the URL)
├── app-ads.txt           AdMob authorised sellers — do not change
├── robots.txt, sitemap.xml
├── .nojekyll             tells GitHub Pages to serve files as they are
├── favicon.ico, favicon.png, apple-touch-icon.png
├── assets/
│   ├── site.css          all styling (light + dark mode)
│   ├── site.js           remembers the chosen language, small UI helpers
│   └── img/              optimised screenshots, fox mascot, app icon, og-image.jpg
├── en/  tr/  de/  fr/  es/  it/  ru/  zh/  ja/  ko/
│   ├── index.html        product page
│   ├── privacy/index.html
│   ├── terms/index.html
│   └── support/index.html
└── _build/               tools for editing (not needed by visitors)
    ├── i18n/<lang>.json  ALL texts, one file per language (en.json is the source)
    ├── build.py          regenerates every HTML page from the JSON files
    ├── check_i18n.py     checks that every translation matches en.json's structure
    ├── verify.py         crawls the built site: links, anchors, HTML structure, hreflang
    └── make_redirects.py only for moving to another host (see the checklist below)
```

The shipped app links to these pages on the original host: `https://promptmasterapp.github.io/<lang>/privacy/`,
`/terms/` and `/support/` (see `SITE` in `promptmaster/src/yasal.ts`). **Keep these
paths stable.**

## Preview locally

```sh
cd promptmaster-site
python3 -m http.server 8000
# open http://localhost:8000/
```

Use a local server, not `file://`, because links point to folders (`privacy/`).

## Editing texts

All texts live in `_build/i18n/<lang>.json`. Pages are generated from these files,
so one edit fixes the text everywhere it appears.

1. Edit the text in `_build/i18n/en.json` **and the same key in the other nine
   files**. Legal texts (privacy, terms) must say the same thing in every language.
2. Run:
   ```sh
   python3 _build/check_i18n.py   # structure, links and placeholders match en.json
   python3 _build/build.py        # rewrites all HTML pages
   python3 _build/verify.py       # every link, anchor, hreflang and page is OK
   ```
3. Commit and push. GitHub Pages updates in about a minute.

**Small markup used in the JSON texts:**

| Write | Result |
| --- | --- |
| `**bold**` | **bold** (used for in-app menu names such as **Profile → Reset progress**) |
| `[text](https://…)` | a link |
| `[text]({support})` | link to this language's Support page (`{privacy}`, `{terms}`, `{home}` also work) |
| A string starting with `- ` | bullet point (consecutive ones form a list) |
| A string starting with `### ` | small heading |
| A string starting with `! ` | highlighted box |
| `<em>…</em>` | only in `home.heroTitle`: the orange, underlined word(s) |

Never type ASCII double quotes `"` inside a text; they break the JSON. Use typographic
quotes (“ ” „ “ « » 「 」).

**Legal pages.** The "Last updated" date is `common.lastUpdated` in each JSON file,
plus `LAST_MOD` in `_build/build.py` (used for `<time>` and the sitemap). Update
both whenever the policy or terms change.

**Quick fixes without Python.** You can also edit an HTML file directly. But
`build.py` overwrites every HTML file the next time it runs, so copy the change into
the JSON as well.

**Adding a language.** Copy `en.json` to `<code>.json` and translate it (keep the
`id`/`key`/`todo` values). Add the code to `LANGS` in `build.py`, `check_i18n.py` and
`verify.py`, then run the three commands above. For a non-Latin script, also add a
font stack in `assets/site.css`, as `ru`/`zh`/`ja`/`ko` have.

**Images.** Screenshots are `assets/img/screen-0N.webp` (560 px wide). They are cut
from the store screenshots with the headline removed, and the page draws the phone
frame in CSS. To replace one, export a WebP of the same size, under ~100 KB. The
current screenshots show the Turkish UI on every language's page. Localised ones can
be added later (e.g. `screen-01-de.webp`, then change `page_home` in `build.py`).

## Things the owner still has to do

- [ ] **Store badges.** Every page's `Download on the App Store` / `Get it on Google Play`
      buttons link to `#` and have a `<!-- TODO -->` comment next to them. When the app
      is live, put the real URLs in `store_badges()` in `_build/build.py`.
      Google Play: `https://play.google.com/store/apps/details?id=com.caly.promptmaster`.
      App Store: `https://apps.apple.com/app/id<numeric id>`. Then rebuild. Ideally
      replace the buttons with the official localised badge artwork from
      Apple and Google.
- [ ] **Legal review** (search for `TODO legal review` in the HTML or JSON):
      governing law (Türkiye) in the Terms, the legal bases in the Privacy Policy, and
      the postal address/legal form of Tiki Studios as data controller.
- [ ] Make sure the Privacy Policy matches what ships. It describes Google AdMob,
      Firebase (Analytics, Crashlytics, Remote Config) and RevenueCat. If an SDK is
      added or removed, update the policy before releasing that version.

## Moving to a custom domain — checklist

Example: moving to `promptmaster.app`. Do the steps in order.

1. **Buy the domain** at any registrar.
2. **Tell GitHub Pages about it.**
   - In the repo: *Settings → Pages → Custom domain* → `promptmaster.app` → Save.
     This commits a file named `CNAME` containing `promptmaster.app` to the repo
     root. You can also add that file yourself: one line, no `https://`.
   - Recommended: verify the domain under your GitHub account/organisation settings
     (*Settings → Pages → Add a domain*). This stops anyone else from claiming it.
3. **DNS records** at your registrar:
   - Apex domain `promptmaster.app`:
     - `A` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
     - `AAAA` → `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `www` subdomain: `CNAME` → `promptmasterapp.github.io`
   - Remove any other A/AAAA/CNAME records for these names, such as the
     registrar's "parking" records.
4. **HTTPS.** Wait until *Settings → Pages* shows the DNS check as successful.
   GitHub then issues the certificate, which can take up to 24 hours. Tick
   **Enforce HTTPS**.
5. **Replace the absolute base URL.** It appears only in `<link rel="canonical">`,
   `hreflang`, Open Graph tags, the JSON-LD block, `sitemap.xml`, `robots.txt` and
   the `BASE` constants of the `_build` scripts. Every other link is relative. Run
   this once from the repo root:
   ```sh
   # macOS
   grep -rlF 'https://promptmaster.tikistudios.io' --include='*.html' --include='*.xml' --include='*.txt' --include='*.py' . \
     | xargs sed -i '' 's#https://promptmasterapp\.github\.io#https://promptmaster.app#g'
   # Linux: same command with  sed -i  instead of  sed -i ''
   python3 _build/verify.py
   ```
   Commit and push. (Equivalent: change `BASE` in `_build/build.py`, `_build/verify.py`
   and run `build.py`.)
6. **Update the app.** In `promptmaster/src/yasal.ts`, set
   `export const SITE = 'https://promptmaster.app';` and ship an app update.
   Versions already installed keep opening the old github.io links, so step 9 matters.
7. **Update the stores and AdMob.**
   - **App Store Connect:** *App Privacy → Privacy Policy URL*, plus the optional
     *User Privacy Choices URL*. Also each localisation's **Support URL** and
     **Marketing URL** on the version page (for example `https://promptmaster.app/de/support/`).
   - **Google Play Console:** *Policy and programs → App content → Privacy policy*.
     Also *Store presence → Store settings → Store listing contact details →
     Website*.
   - **AdMob `app-ads.txt`:** AdMob looks for `app-ads.txt` at the root of the
     *developer website* listed in the App Store (Marketing URL) and on Google Play
     (Website). Set both to `https://promptmaster.app`. Check that
     `https://promptmaster.app/app-ads.txt` loads, then in AdMob *Apps → app-ads.txt*
     click *Check for updates*. Verification can take a day.
   - **AdMob privacy messages:** in *Privacy & messaging*, open the European
     regulations (GDPR) message, and the US states message if you use one. Change
     each app's **Privacy policy URL** to the new address and publish the message
     again.
8. **Search engines (optional).** Add the new domain in Google Search Console and
   submit `https://promptmaster.app/sitemap.xml`.
9. **Keep the old github.io addresses working.**
   - **Same repo (normal case):** once this repo has the `CNAME`, GitHub
     automatically sends `https://promptmaster.tikistudios.io/<any path>` to
     `https://promptmaster.app/<same path>` with a permanent (301) redirect. Keep this
     repository and its Pages setting. Do **not** delete or rename it, or the old
     links in released apps and store listings stop working.
   - **New domain served somewhere else** (another repo or host): GitHub Pages cannot
     configure server-side redirects, so this repo must stay online as redirect
     stubs. In a checkout of this repo, run
     `python3 _build/make_redirects.py https://promptmaster.app`. It rewrites every
     page into a small HTML file with `<meta http-equiv="refresh" content="0; url=…">`,
     a canonical link, and a JavaScript redirect that keeps the path and `#anchor`.
     Then commit and push. Search engines treat a 0-second meta refresh like a
     permanent redirect. Keep `app-ads.txt` in this repo until AdMob has verified the
     new domain.

## Checks before publishing

```sh
python3 _build/check_i18n.py && python3 _build/build.py && python3 _build/verify.py
```

`verify.py` confirms that all 40 language pages, the chooser and the 404 page exist,
that every internal `href`/`src` and `#anchor` resolves, that the HTML is balanced
with one `<h1>`, unique ids and `alt` on every image, and that the hreflang, canonical,
sitemap and `app-ads.txt` are correct.

## Contact

support@tikistudios.io
