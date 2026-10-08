# bigbeautifulbrain.si

Static website for Big Beautiful Brain. Repository `brainsi/bigbeautifulbrain.si`, published by
GitHub Pages from the `main` branch (folder `/`) at https://bigbeautifulbrain.si. No framework and
no dependencies beyond Python 3.9 or later.

## Layout

| Path | What it is |
|---|---|
| `_src/pages/*.html` | Page bodies. Each starts with a JSON comment: output path, title, description, sub-navigation, and `noindex` where a page stays out of search. |
| `_src/build.py` | Wraps every page in the shared head, header, menu and footer, resolves the `{{root}}`, `{{arrow}}`, `{{email}}`, `{{site}}`, `{{form_post}}`, `{{form_ajax}}` and `{{img name width}}` tokens, adds content hashes to the CSS and JS links, writes `sitemap.xml`, and fails on dashes, banned phrases or unresolved tokens. |
| `assets/css/site.css` | The design system. |
| `assets/js/site.js` | Menu, scroll reveal, hero brain canvas, tabs, sticky steps, carousel, counters, section navigation, contact form. |
| `*.html`, `insights/` | Built pages. Do not edit them by hand; edit `_src/pages` and rebuild. |
| `CNAME` | The custom domain for GitHub Pages. |
| `_config.yml` | Keeps `_src`, `_scratch` and this file out of the published site. |

## Build, preview, publish

```bash
python3 _src/build.py
python3 -m http.server 4173 --bind 127.0.0.1
```

Open http://localhost:4173 to review. Rebuild after every change to `_src`, `site.css` or
`site.js`, so the hashed links change and browsers fetch the new files. Commit the source and the
built pages together and push to `main`; GitHub Pages republishes in about a minute. To check a
deployment:

```bash
gh api repos/brainsi/bigbeautifulbrain.si/pages/builds/latest --jq '.status'
```

## Contact form

The form on `contact.html` posts through FormSubmit (formsubmit.co), which emails every submission
to `neural@bigbeautifulbrain.si` (set by `EMAIL` in `_src/build.py`). With JavaScript the page
sends JSON to `https://formsubmit.co/ajax/neural@bigbeautifulbrain.si` and shows the result in
place; without JavaScript the browser posts to `https://formsubmit.co/neural@bigbeautifulbrain.si`
and lands on `thanks.html`. A hidden `_honey` field drops bot submissions. If sending fails, the
page asks the visitor to email the address directly.

One-time activation: the first submission makes FormSubmit send an "Activate Form" email to
`neural@bigbeautifulbrain.si`. Nothing is delivered until that link is clicked, so the domain's
mail must be working first (see Email below). After activation, FormSubmit can also issue a random
alias to use in place of the address in the two form URLs.

## DNS at Namecheap

Domain List, `bigbeautifulbrain.si`, Manage. On the Domain tab, Nameservers must be "Namecheap
BasicDNS". On the Advanced DNS tab, delete the default parking records (the `www` CNAME to
`parkingpage.namecheap.com` and the `@` URL Redirect), then add:

| Type | Host | Value | TTL |
|---|---|---|---|
| A Record | `@` | `185.199.108.153` | Automatic |
| A Record | `@` | `185.199.109.153` | Automatic |
| A Record | `@` | `185.199.110.153` | Automatic |
| A Record | `@` | `185.199.111.153` | Automatic |
| AAAA Record | `@` | `2606:50c0:8000::153` | Automatic |
| AAAA Record | `@` | `2606:50c0:8001::153` | Automatic |
| AAAA Record | `@` | `2606:50c0:8002::153` | Automatic |
| AAAA Record | `@` | `2606:50c0:8003::153` | Automatic |
| CNAME Record | `www` | `brainsi.github.io.` | Automatic |
| TXT Record | `_github-pages-challenge-brainsi` | the code GitHub shows (below) | Automatic |

The TXT record verifies the domain for the `brainsi` organization, so no other GitHub account can
publish on it: github.com/organizations/brainsi/settings/pages, "Add a domain",
`bigbeautifulbrain.si`, copy the value, add the record, then press Verify.

## Email

On the Advanced DNS tab, Mail Settings: choose "Email Forwarding" (Namecheap adds the MX and SPF
records). On the Domain tab, Redirect Email: add a forwarder from `neural` to the inbox that should
receive enquiries. A mailbox product (Namecheap Private Email, Google Workspace) works as well; use
its MX records instead.

## HTTPS

When DNS resolves, GitHub issues the certificate (usually within an hour). Then tick "Enforce
HTTPS" in the repository's Pages settings, or:

```bash
gh api -X PUT repos/brainsi/bigbeautifulbrain.si/pages -F https_enforced=true
```

## Open items

1. The pages load 15 photos from images.unsplash.com (the IDs are in `IMAGES` in
   `_src/build.py`). To self-host them, download them into `assets/img/photos/` and point
   `img_url()` at the local files. The Unsplash licence allows this without attribution.
2. Review the founder bio on `about.html`, the first-deployment numbers and the reference line on
   the home page, and the pricing language.
