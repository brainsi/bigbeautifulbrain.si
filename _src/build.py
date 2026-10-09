#!/usr/bin/env python3
"""Build the Big Beautiful Brain static site.

Page bodies live in _src/pages/*.html. Each starts with a one-line JSON header in an HTML
comment: <!--{"out": "index.html", "title": "...", "description": "...", "subnav": [...]}-->
This script wraps every body in the shared head, header, menu and footer, resolves the
{{root}} prefix for relative links and the {{img name width}} photo tokens, and writes the
pages to the repository root, ready for GitHub Pages. Run: python3 _src/build.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_src', 'pages')
SITE = 'https://bigbeautifulbrain.si'
EMAIL = 'neural@bigbeautifulbrain.si'
# The contact form posts through FormSubmit (formsubmit.co), which emails every submission to EMAIL.
# FORM_POST is the plain POST used without JavaScript; FORM_AJAX is the JSON endpoint site.js uses.
FORM_POST = 'https://formsubmit.co/' + EMAIL
FORM_AJAX = 'https://formsubmit.co/ajax/' + EMAIL

# Photography: Unsplash (free licence). Hotlinked for review; self-host before launch.
IMAGES = {
    'port_dusk': 'photo-1590496793907-4d66e2994b4d',
    'leader_window': 'photo-1523504706857-0b1cc4956993',
    'boardroom': 'photo-1594291714464-252c9da8447a',
    'interview': 'photo-1573496546038-82f9c39f6365',
    'warehouse': 'photo-1644079446600-219068676743',
    'factory': 'photo-1764185800646-f75f7e16e465',
    'aerial': 'photo-1715026323215-a2dbb71272f6',
    'building_dusk': 'photo-1702549245122-2700421f8b77',
    'building_warm': 'photo-1600849201385-980094c9037a',
    'datacenter': 'photo-1580106815433-a5b1d1d53d85',
    'team_table': 'photo-1573164574572-cb89e39749b4',
    'port_moody': 'photo-1590497008432-598f04441de8',
    'group_window': 'photo-1638312105950-27539b2efce4',
    'glass_facade': 'photo-1660496247667-3fb697c396af',
    'empty_hall': 'photo-1772305336606-989a457ffbae',
}


def img_url(name, width):
    return f'https://images.unsplash.com/{IMAGES[name]}?auto=format&fit=crop&w={width}&q=80'


ARROW = ('<svg class="arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h11M9 4l4 4-4 4" fill="none" '
         'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')
MARK = ('<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" fill="#0b1b2b"/>'
        '<g fill="none" stroke="#8ef5c9" stroke-width="1.5" stroke-linecap="round" opacity=".85">'
        '<path d="M8.5 18.5 13.5 11l5.5 3.5 4.5-5.5M13.5 11 12.5 21.5l6.5-7.5 3.5 7M8.5 18.5l4 3h10l1.5-6.5-5-1"/></g>'
        '<g fill="#f4f1ec"><circle cx="8.5" cy="18.5" r="1.9"/><circle cx="13.5" cy="11" r="1.9"/><circle cx="23.5" cy="8.5" r="1.5"/>'
        '<circle cx="12.5" cy="21.5" r="1.7"/><circle cx="22.5" cy="21.5" r="1.7"/><circle cx="24" cy="15" r="1.5"/></g>'
        '<circle cx="19" cy="14.5" r="2.4" fill="#8ef5c9"/></svg>')
BURGER = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 6h14M3 10h14M3 14h14" stroke="#0b1b2b" '
          'stroke-width="1.6" stroke-linecap="round"/></svg>')
CLOSE = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15" stroke="#0b1b2b" '
         'stroke-width="1.6" stroke-linecap="round"/></svg>')
CHEV = ('<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M6 3l5 5-5 5" fill="none" '
        'stroke="#8b939b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')

SERVICES = [
    ('what-we-do.html#diligence', 'Diligence Brain', 'Operating reality before you sign'),
    ('what-we-do.html#hundred-days', '100-Day Brain', 'The value creation plan, made visible'),
    ('what-we-do.html#operate', 'Operating Brain', 'One source of truth through the hold'),
    ('what-we-do.html#grow', 'Growth Brain', 'Add-ons captured into the platform'),
    ('what-we-do.html#exit', 'Exit Brain', 'Evidence organized for the sale'),
    ('what-we-do.html#portfolio', 'Portfolio Brain', 'A fund-level view across companies'),
]
PLATFORM = [
    ('platform.html#anatomy', 'Anatomy of a Business Brain', 'Eight layers, cited facts, human review'),
    ('platform.html#agents', 'The agent runtime', 'Runners, routers, models, skills, connections'),
    ('platform.html#connections', 'MCP, RAG and API', 'How the brain reaches your systems and your sponsor'),
    ('platform.html#governance', 'Governance and security', 'Access levels, audit trail, ownership'),
]
WORK = [
    ('how-we-work.html#phases', 'How an engagement runs', 'Scope, capture, diagnose, act, compound'),
    ('how-we-work.html#team', 'The forward-deployed team', 'Interviews, data discovery, heavy lifting'),
    ('how-we-work.html#models', 'Ways to start', 'Pilot, 100 days, subscription'),
    ('how-we-work.html#faq', 'Questions we hear', 'Ownership, models, data, time'),
]
COMPANY = [
    ('about.html', 'About us', 'Why we built Big Beautiful Brain'),
    ('insights/index.html', 'Insights', 'Perspectives on owning and running businesses'),
    ('contact.html', 'Contact', 'Start with one portfolio company'),
]


def menu_html(r):
    def subs(items):
        return ''.join(f'<a href="{r}{h}">{t}</a>' for h, t, _ in items)

    def details(items):
        return ''.join(f'<a href="{r}{h}">{t}<span>{d}</span></a>' for h, t, d in items)
    groups = [('services', 'What we do', SERVICES, 'Across the deal lifecycle',
               'We work where the deal needs the understanding most, from the first look at a data room to the last buyer meeting.'),
              ('platform', 'The Brain', PLATFORM, 'A platform, not a report',
               'A living knowledge graph of the company and an agent runtime that works on it every day.'),
              ('work', 'How we work', WORK, 'Agents and people, together',
               'A swarm of agents does the reading and the analysis; our team does the interviews and the heavy lifting.'),
              ('company', 'Company', COMPANY, 'Big Beautiful Brain',
               'AI-native services for private equity and corporate acquirers.')]
    nav = ''.join(f'<div class="menu-group"><button type="button" data-detail="{g}" aria-expanded="false">{label}{CHEV}</button>'
                  f'<div class="menu-sub">{subs(items)}</div></div>' for g, label, items, _, _ in groups)
    panels = ''.join(f'<div data-panel="{g}"{" hidden" if i else ""}><p class="eyebrow dim">{label}</p><h3>{head}</h3>'
                     f'<p class="small">{blurb}</p><div class="grid g2">{details(items)}</div></div>'
                     for i, (g, label, items, head, blurb) in enumerate(groups))
    promo = (f'<aside class="menu-promo"><div class="media"><img src="{img_url("interview", 900)}" alt="Two colleagues in conversation by a window" loading="lazy"></div>'
             f'<p class="eyebrow dim">Perspective</p><h4>Why the first 100 days decide the hold</h4>'
             f'<p class="small">What a new owner needs to know in the first month, and why most of it is not in the data room.</p>'
             f'<div><a class="btn" href="{r}insights/first-100-days.html">Read the perspective {ARROW}</a></div></aside>')
    return (f'<div class="menu" id="menu" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Site menu">'
            f'<div class="menu-top"><button class="menu-btn" type="button" data-menu-close aria-label="Close menu">{CLOSE}</button>'
            f'<a class="brand" href="{r}index.html">{MARK}<span class="brand-name">Big Beautiful Brain</span></a>'
            f'<span class="spacer"></span><a class="btn" href="{r}contact.html">Start a pilot {ARROW}</a></div>'
            f'<div class="menu-body"><nav class="menu-nav" aria-label="Main">{nav}</nav>'
            f'<div class="menu-detail">{panels}</div>{promo}</div></div>')


def header_html(r, subnav, out):
    sub = ''
    if subnav:
        label, links = subnav['label'], subnav['links']
        cur = ' class="is-current"'
        sub = '<nav class="pill subnav" aria-label="On this page"><span class="label">' + label + '</span>' + ''.join(
            '<a href="' + h + '"' + (cur if i == 0 else '') + '>' + t + '</a>' for i, (t, h) in enumerate(links)) + '</nav>'
    return (f'<a class="skip-link" href="#main">Skip to content</a>'
            f'<header class="site-header"><div class="bar">'
            f'<div class="pill"><button class="menu-btn" type="button" data-menu-open aria-controls="menu" aria-expanded="false" aria-label="Open menu">{BURGER}</button>'
            f'<a class="brand" href="{r}index.html" aria-label="Big Beautiful Brain home">{MARK}<span class="brand-name">Big Beautiful Brain</span></a></div>'
            f'{sub}'
            f'<div class="pill header-actions"><a class="text-link" href="{r}insights/index.html">Insights</a>'
            f'<a class="btn" href="{r}contact.html">Start a pilot {ARROW}</a></div>'
            f'</div></header>')


def footer_html(r):
    def lst(items):
        return '<ul>' + ''.join(f'<li><a href="{r}{h}">{t}</a></li>' for h, t, _ in items) + '</ul>'
    return (f'<footer class="site-footer"><div class="container"><div class="footer-grid">'
            f'<div><a class="footer-brand brand" href="{r}index.html">{MARK}<span class="brand-name">Big Beautiful Brain</span></a>'
            f'<p class="footer-blurb">AI-native services for private equity and corporate acquirers. We get you to a clear picture of a business '
            f'in weeks, and keep that understanding working for you from diligence to exit.</p>'
            f'<a class="btn" href="{r}contact.html">Start a pilot {ARROW}</a></div>'
            f'<div><h4>What we do</h4>{lst(SERVICES)}</div>'
            f'<div><h4>The Brain</h4>{lst(PLATFORM)}</div>'
            f'<div><h4>Company</h4>{lst(COMPANY + [("how-we-work.html", "How we work", "")])}</div>'
            f'</div><div class="footer-bottom"><span>&copy; <span data-year>2026</span> Big Beautiful Brain &middot; '
            f'<a href="mailto:{EMAIL}">{EMAIL}</a></span><span>bigbeautifulbrain.si &middot; Photography: Unsplash</span></div>'
            f'</div></footer>')


def asset_version(rel):
    import hashlib
    return hashlib.sha1(open(os.path.join(ROOT, rel), 'rb').read()).hexdigest()[:10]


def page(meta, body):
    out = meta['out']
    depth = out.count('/')
    # GitHub Pages serves 404.html at whatever path was missing, so it needs root-absolute links
    r = '/' if out == '404.html' else '../' * depth
    canonical = SITE + '/' + ('' if out == 'index.html' else out.replace('index.html', ''))
    title = meta['title'] if meta.get('bare_title') else f"{meta['title']} | Big Beautiful Brain"
    og_img = img_url(meta.get('og', 'port_dusk'), 1200)
    head = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{title}</title><meta name="description" content="{meta["description"]}">'
            + ('<meta name="robots" content="noindex">' if meta.get('noindex') or out == '404.html' else '') +
            f'<link rel="canonical" href="{canonical}">'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="Big Beautiful Brain">'
            f'<meta property="og:title" content="{title}"><meta property="og:description" content="{meta["description"]}">'
            f'<meta property="og:url" content="{canonical}"><meta property="og:image" content="{og_img}">'
            '<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0b1b2b">'
            f'<link rel="icon" href="{r}assets/img/favicon.svg" type="image/svg+xml">'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500&display=swap" rel="stylesheet">'
            '<link rel="preconnect" href="https://images.unsplash.com">'
            f'<link rel="stylesheet" href="{r}assets/css/site.css?v={asset_version("assets/css/site.css")}"></head><body>')
    html = (head + header_html(r, meta.get('subnav'), out) + menu_html(r) + f'<main id="main">{body}</main>'
            + footer_html(r) + f'<script src="{r}assets/js/site.js?v={asset_version("assets/js/site.js")}" defer></script></body></html>')
    html = html.replace('{{root}}', r).replace('{{arrow}}', ARROW).replace('{{email}}', EMAIL)
    html = html.replace('{{form_post}}', FORM_POST).replace('{{form_ajax}}', FORM_AJAX).replace('{{site}}', SITE)
    html = re.sub(r'\{\{img (\w+) (\d+)\}\}', lambda m: img_url(m.group(1), int(m.group(2))), html)
    return out, html


def main():
    built, problems = [], []
    for path in sorted(glob.glob(os.path.join(SRC, '*.html'))):
        raw = open(path, encoding='utf-8').read()
        m = re.match(r'\s*<!--(\{.*?\})-->\s*', raw, re.S)
        if not m:
            problems.append(f'{path}: missing JSON header')
            continue
        meta = json.loads(m.group(1))
        out, html = page(meta, raw[m.end():])
        for bad in ('—', '–'):
            if bad in html:
                problems.append(f'{out}: contains a dash character U+{ord(bad):04X}')
        for word in ('honest', 'load-bearing', 'load bearing'):
            if re.search(r'\b' + word, html, re.I):
                problems.append(f'{out}: contains banned phrase "{word}"')
        left = re.findall(r'\{\{[^}]*\}\}', html)
        if left:
            problems.append(f'{out}: unresolved tokens {left[:3]}')
        dest = os.path.join(ROOT, out)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(html)
        built.append(out)
    urls = ''.join(f'<url><loc>{SITE}/{"" if o == "index.html" else o.replace("index.html", "")}</loc></url>'
                   for o in built if o not in ('404.html', 'thanks.html'))
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    print('built', len(built), 'pages:', ', '.join(built))
    for p in problems:
        print('PROBLEM', p)
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
