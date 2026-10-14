#!/usr/bin/env python3
"""Build the Big Beautiful Brain static site.

Page bodies live in _src/pages/*.html. Each starts with a one-line JSON header in an HTML
comment: <!--{"out": "index.html", "title": "...", "description": "...", "audience": "pe", "subnav": [...]}-->
The audience ("pe" for private equity, "rg" for restaurant and hospitality groups, "all" for the
gateway and the shared pages) picks the menu, the footer, the header switch and the contact link.
This script wraps every body in the shared head, header, menu and footer, resolves the {{root}}
prefix for relative links and the {{img name width}} photo tokens, writes redirect stubs for moved
pages, and writes everything to the repository root, ready for GitHub Pages. Run: python3 _src/build.py
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
    'pe_skyline': 'photo-1783361522077-f167aed72ea3',
    # restaurant and hospitality groups
    'rg_dining': 'photo-1552960226-639240203497',
    'rg_window': 'photo-1775144581014-bf6cb3ab9f06',
    'rg_floor': 'photo-1559329007-40df8a9345d8',
    'rg_room': 'photo-1517248135467-4c7edcad34c4',
    'rg_city_room': 'photo-1653259038915-7cf0b7a4dd6c',
    'rg_line': 'photo-1769955817432-641929f613f0',
    'rg_pass': 'photo-1785068540682-6917367db28e',
    'rg_plating': 'photo-1577106263724-2c8e03bfe9cf',
    'rg_long_table': 'photo-1536392706976-e486e2ba97af',
    'rg_private_room': 'photo-1561065270-5c2af775b542',
    'rg_gala': 'photo-1768508950243-16fd93e88d7f',
    'rg_rooftop': 'photo-1770021601385-af0bf0136762',
    'rg_resort': 'photo-1571003123894-1f0594d2b5d9',
    'rg_terrace': 'photo-1579027989536-b7b1f875659b',
    'rg_bar': 'photo-1572116469696-31de0f17cc34',
    'rg_pour': 'photo-1470337458703-46ad1756a187',
    'rg_host': 'photo-1758519289791-ffce8889ca8c',
}

# Pages that moved. Each old path gets a small page that forwards to the new one, keeping the #fragment.
REDIRECTS = {
    'what-we-do.html': 'private-equity/what-we-do.html',
    'how-we-work.html': 'private-equity/how-we-work.html',
    'platform.html': 'approach.html',
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

PE_SERVICES = [
    ('private-equity/what-we-do.html#diligence', 'Diligence', 'The operating reality before you sign'),
    ('private-equity/what-we-do.html#hundred-days', 'The first 100 days', 'The value creation plan, made visible'),
    ('private-equity/what-we-do.html#operate', 'Through the hold', 'One picture for the board and management'),
    ('private-equity/what-we-do.html#grow', 'Buy and build', 'Add-ons absorbed into the platform'),
    ('private-equity/what-we-do.html#exit', 'Exit', 'Evidence organized for the sale'),
    ('private-equity/what-we-do.html#portfolio', 'Across the fund', 'Every company read the same way'),
]
PE_WORK = [
    ('private-equity/how-we-work.html#phases', 'How an engagement runs', 'Scope, capture, diagnose, act, measure'),
    ('private-equity/how-we-work.html#team', 'The forward-deployed team', 'Interviews, data discovery, heavy lifting'),
    ('private-equity/how-we-work.html#models', 'Ways to start', 'Pilot, deal engagement, subscription'),
    ('private-equity/how-we-work.html#faq', 'Questions we hear', 'Ownership, models, data, time'),
]
RG_SERVICES = [
    ('restaurant-groups/what-we-do.html#acquire', 'Acquiring a concept or a group', 'What each venue really earns, before you sign'),
    ('restaurant-groups/what-we-do.html#absorb', 'The first 90 days', 'Absorb a concept without losing what made it work'),
    ('restaurant-groups/what-we-do.html#operate', 'Every venue, one picture', 'Prime cost, labor and guests across the group'),
    ('restaurant-groups/what-we-do.html#portfolio', 'Portfolio optimization', 'Remodel, convert or close on venue-level evidence'),
    ('restaurant-groups/what-we-do.html#guests', 'Private events, catering and regulars', 'The revenue that compounds, followed through'),
    ('restaurant-groups/what-we-do.html#people', 'People and know-how', 'Keep what your best people know'),
    ('restaurant-groups/what-we-do.html#sell', 'Recapitalization or sale', 'Evidence organized before the process begins'),
]
RG_WORK = [
    ('restaurant-groups/how-we-work.html#phases', 'How an engagement runs', 'Two weeks to a working picture of the group'),
    ('restaurant-groups/how-we-work.html#team', 'The team on site', 'Kitchens, floors, offices and systems'),
    ('restaurant-groups/how-we-work.html#models', 'Ways to start', 'One concept, one region or the whole group'),
    ('restaurant-groups/how-we-work.html#faq', 'Questions we hear', 'Systems, management time, ownership'),
]
APPROACH = [
    ('approach.html#ains', 'AI-native services', 'Outcomes delivered by agents and a senior team'),
    ('approach.html#agents', 'Persistent agents', 'Agents that stay with a journey for months'),
    ('approach.html#brain', 'The Business Brain', 'Every fact cited and reviewed'),
    ('approach.html#governance', 'Governance and ownership', 'Access levels, audit trail, export'),
]
COMPANY = [
    ('about.html', 'About us', 'Why we built Big Beautiful Brain'),
    ('insights/index.html', 'Insights', 'Perspectives on owning and running businesses'),
    ('contact.html', 'Contact', 'Start with one company or one group'),
]
PE_SITE = [
    ('private-equity/index.html', 'Overview', 'For partners at private equity firms'),
    ('private-equity/what-we-do.html', 'What we do', 'From diligence to exit'),
    ('private-equity/how-we-work.html', 'How we work', 'Two weeks to a working brain'),
]
RG_SITE = [
    ('restaurant-groups/index.html', 'Overview', 'For partners at restaurant and hospitality groups'),
    ('restaurant-groups/what-we-do.html', 'What we do', 'From acquisition to the next transaction'),
    ('restaurant-groups/how-we-work.html', 'How we work', 'Two weeks to a working picture'),
]

APPROACH_GROUP = ('approach', 'Our approach', APPROACH, 'AI-native services',
                  'Outcomes delivered by persistent agents and a small senior team, working from a brain the business owns.')
COMPANY_GROUP = ('company', 'Company', COMPANY, 'Big Beautiful Brain',
                 'AI-native services for private equity firms and for restaurant and hospitality groups.')

AUDIENCES = {
    'pe': {
        'contact': 'contact.html?for=pe',
        'groups': [('services', 'What we do', PE_SERVICES, 'Across the deal lifecycle',
                    'We work where the deal needs the understanding most, from the first look at a data room to the last buyer meeting.'),
                   ('work', 'How we work', PE_WORK, 'Agents and people, together',
                    'A swarm of agents does the reading and the analysis; our team does the interviews and the heavy lifting.'),
                   APPROACH_GROUP, COMPANY_GROUP],
        'promo': ('interview', 'Two colleagues in conversation by a window', 'Perspective', 'Why the first 100 days decide the hold',
                  'What a new sponsor needs to know in the first month, and why most of it is not in the data room.',
                  'insights/first-100-days.html'),
        'blurb': 'AI-native services for private equity sponsors and corporate acquirers. We get you to a clear picture of each company '
                 'you back in weeks, and keep that understanding working for you from diligence to exit.',
        'cols': [('What we do', PE_SERVICES), ('Our approach', APPROACH),
                 ('Company', COMPANY + [('private-equity/how-we-work.html', 'How we work', ''),
                                        ('restaurant-groups/index.html', 'For restaurant groups', '')])],
    },
    'rg': {
        'contact': 'contact.html?for=rg',
        'groups': [('services', 'What we do', RG_SERVICES, 'From acquisition to the next transaction',
                    'We work where the group needs the understanding most: acquisitions, integration, operations, openings, conversions and the next transaction.'),
                   ('work', 'How we work', RG_WORK, 'On the floor and in the systems',
                    'Agents read the POS, the invoices and the schedules; our team works the kitchens, the floors and the offices.'),
                   APPROACH_GROUP, COMPANY_GROUP],
        'promo': ('rg_pass', 'Chefs working the pass of an open kitchen', 'Perspective', 'The first 90 days after a concept joins the group',
                  'What the group needs to learn before the regulars notice, and why most of it lives with the chef and the GM.',
                  'insights/first-90-days-restaurant.html'),
        'blurb': 'AI-native services for restaurant and hospitality groups. When a concept joins the group, we get you to a clear '
                 'picture of it in weeks, and keep that understanding working through every opening, acquisition and transaction.',
        'cols': [('What we do', RG_SERVICES), ('Our approach', APPROACH),
                 ('Company', COMPANY + [('restaurant-groups/how-we-work.html', 'How we work', ''),
                                        ('private-equity/index.html', 'For private equity', '')])],
    },
    'all': {
        'contact': 'contact.html',
        'groups': [('pe', 'Private equity', PE_SITE, 'For partners at private equity firms',
                    'A living brain for every company you back, from the first look at the data room to the exit.'),
                   ('rg', 'Restaurant groups', RG_SITE, 'For partners at restaurant and hospitality groups',
                    'Restaurants, nightlife, events and destinations: integrate every concept that joins the group and grow on venue-level evidence.'),
                   APPROACH_GROUP, COMPANY_GROUP],
        'promo': ('glass_facade', 'Office windows lit at night', 'Perspective', 'Agents that stay',
                  'Why the agents that create value follow one journey for months, and what they need to do it well.',
                  'insights/agents-that-stay.html'),
        'blurb': 'AI-native services for acquisitions, mergers and new ventures, for private equity sponsors and hospitality groups. '
                 'We get you to a clear picture of each new investment in weeks, and keep that understanding working through to the next transaction.',
        'cols': [('Private equity', PE_SITE), ('Restaurant groups', RG_SITE), ('Our approach', APPROACH), ('Company', COMPANY)],
    },
}


def switch_html(r, aud, cls):
    """The two-way switch between the private equity and restaurant group sites."""
    links = [('pe', 'private-equity/index.html', 'Private equity'), ('rg', 'restaurant-groups/index.html', 'Restaurant groups')]
    on = ' class="is-on" aria-current="true"'
    return (f'<nav class="{cls}" aria-label="Choose your industry">' + ''.join(
        f'<a href="{r}{h}"{on if a == aud else ""}>{t}</a>' for a, h, t in links) + '</nav>')


def menu_html(r, aud):
    cfg = AUDIENCES[aud]

    def subs(items):
        return ''.join(f'<a href="{r}{h}">{t}</a>' for h, t, _ in items)

    def details(items):
        return ''.join(f'<a href="{r}{h}">{t}<span>{d}</span></a>' for h, t, d in items)
    groups = cfg['groups']
    nav = ''.join(f'<div class="menu-group"><button type="button" data-detail="{g}" aria-expanded="false">{label}{CHEV}</button>'
                  f'<div class="menu-sub">{subs(items)}</div></div>' for g, label, items, _, _ in groups)
    panels = ''.join(f'<div data-panel="{g}"{" hidden" if i else ""}><p class="eyebrow dim">{label}</p><h3>{head}</h3>'
                     f'<p class="small">{blurb}</p><div class="grid g2">{details(items)}</div></div>'
                     for i, (g, label, items, head, blurb) in enumerate(groups))
    img, alt, kicker, title, text, href = cfg['promo']
    promo = (f'<aside class="menu-promo"><div class="media"><img src="{img_url(img, 900)}" alt="{alt}" loading="lazy"></div>'
             f'<p class="eyebrow dim">{kicker}</p><h4>{title}</h4>'
             f'<p class="small">{text}</p>'
             f'<div><a class="btn" href="{r}{href}">Read the perspective {ARROW}</a></div></aside>')
    return (f'<div class="menu" id="menu" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Site menu">'
            f'<div class="menu-top"><button class="menu-btn" type="button" data-menu-close aria-label="Close menu">{CLOSE}</button>'
            f'<a class="brand" href="{r}index.html">{MARK}<span class="brand-name">Big Beautiful Brain</span></a>'
            f'<span class="spacer"></span>{switch_html(r, aud, "aud-switch in-menu")}'
            f'<a class="btn" href="{r}{cfg["contact"]}">Start a pilot {ARROW}</a></div>'
            f'<div class="menu-body"><nav class="menu-nav" aria-label="Main">{switch_html(r, aud, "aud-switch")}{nav}</nav>'
            f'<div class="menu-detail">{panels}</div>{promo}</div></div>')


def header_html(r, subnav, aud, gateway):
    sub = ''
    if subnav:
        label, links = subnav['label'], subnav['links']
        cur = ' class="is-current"'
        sub = '<nav class="pill subnav" aria-label="On this page"><span class="label">' + label + '</span>' + ''.join(
            '<a href="' + h + '"' + (cur if i == 0 else '') + '>' + t + '</a>' for i, (t, h) in enumerate(links)) + '</nav>'
    # the gateway hero is itself the industry switch, so its header keeps the plain Insights link
    actions = (f'<a class="text-link" href="{r}insights/index.html">Insights</a>' if gateway
               else switch_html(r, aud, 'aud-switch' + (' with-subnav' if subnav else '')))
    return (f'<a class="skip-link" href="#main">Skip to content</a>'
            f'<header class="site-header"><div class="bar">'
            f'<div class="pill"><button class="menu-btn" type="button" data-menu-open aria-controls="menu" aria-expanded="false" aria-label="Open menu">{BURGER}</button>'
            f'<a class="brand" href="{r}index.html" aria-label="Big Beautiful Brain home">{MARK}<span class="brand-name">Big Beautiful Brain</span></a></div>'
            f'{sub}'
            f'<div class="pill header-actions">{actions}'
            f'<a class="btn" href="{r}{AUDIENCES[aud]["contact"]}">Start a pilot {ARROW}</a></div>'
            f'</div></header>')


def footer_html(r, aud):
    cfg = AUDIENCES[aud]

    def lst(items):
        return '<ul>' + ''.join(f'<li><a href="{r}{h}">{t}</a></li>' for h, t, _ in items) + '</ul>'
    cols = ''.join(f'<div><h4>{h}</h4>{lst(items)}</div>' for h, items in cfg['cols'])
    return (f'<footer class="site-footer"><div class="container"><div class="footer-grid cols-{len(cfg["cols"])}">'
            f'<div><a class="footer-brand brand" href="{r}index.html">{MARK}<span class="brand-name">Big Beautiful Brain</span></a>'
            f'<p class="footer-blurb">{cfg["blurb"]}</p>'
            f'<a class="btn" href="{r}{cfg["contact"]}">Start a pilot {ARROW}</a></div>'
            f'{cols}'
            f'</div><div class="footer-bottom"><span>&copy; <span data-year>2026</span> Big Beautiful Brain &middot; '
            f'<a href="mailto:{EMAIL}">{EMAIL}</a></span><span>bigbeautifulbrain.si &middot; Photography: Unsplash</span></div>'
            f'</div></footer>')


def asset_version(rel):
    import hashlib
    return hashlib.sha1(open(os.path.join(ROOT, rel), 'rb').read()).hexdigest()[:10]


def canonical_url(out):
    return SITE + '/' + ('' if out == 'index.html' else out.replace('index.html', ''))


def page(meta, body):
    out = meta['out']
    aud = meta.get('audience', 'all')
    depth = out.count('/')
    # GitHub Pages serves 404.html at whatever path was missing, so it needs root-absolute links
    r = '/' if out == '404.html' else '../' * depth
    canonical = canonical_url(out)
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
            f'<link rel="stylesheet" href="{r}assets/css/site.css?v={asset_version("assets/css/site.css")}"></head>'
            f'<body class="aud-{aud}">')
    html = (head + header_html(r, meta.get('subnav'), aud, meta.get('gateway')) + menu_html(r, aud) + f'<main id="main">{body}</main>'
            + footer_html(r, aud) + f'<script src="{r}assets/js/site.js?v={asset_version("assets/js/site.js")}" defer></script></body></html>')
    html = html.replace('{{root}}', r).replace('{{arrow}}', ARROW).replace('{{email}}', EMAIL)
    html = html.replace('{{contact}}', r + AUDIENCES[aud]['contact'])
    html = html.replace('{{form_post}}', FORM_POST).replace('{{form_ajax}}', FORM_AJAX).replace('{{site}}', SITE)
    html = re.sub(r'\{\{img (\w+) (\d+)\}\}', lambda m: img_url(m.group(1), int(m.group(2))), html)
    return out, html


def redirect_html(old, new):
    rel = '../' * old.count('/') + new
    target = canonical_url(new)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>This page has moved | Big Beautiful Brain</title>'
            f'<meta name="robots" content="noindex"><link rel="canonical" href="{target}">'
            f'<meta http-equiv="refresh" content="0; url={rel}">'
            f'<script>location.replace({json.dumps(rel)} + location.hash)</script></head>'
            f'<body><p>This page has moved to <a href="{rel}">{target}</a>.</p></body></html>')


def main():
    built, problems = [], []
    for path in sorted(glob.glob(os.path.join(SRC, '*.html'))):
        raw = open(path, encoding='utf-8').read()
        m = re.match(r'\s*<!--(\{.*?\})-->\s*', raw, re.S)
        if not m:
            problems.append(f'{path}: missing JSON header')
            continue
        meta = json.loads(m.group(1))
        if meta.get('audience', 'all') not in AUDIENCES:
            problems.append(f'{path}: unknown audience {meta["audience"]!r}')
            continue
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
    for old, new in REDIRECTS.items():
        if new not in built:
            problems.append(f'redirect {old} points to {new}, which was not built')
        if old in built:
            problems.append(f'redirect {old} would overwrite a built page')
        with open(os.path.join(ROOT, old), 'w', encoding='utf-8') as f:
            f.write(redirect_html(old, new))
    urls = ''.join(f'<url><loc>{canonical_url(o)}</loc></url>' for o in built if o not in ('404.html', 'thanks.html'))
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    print('built', len(built), 'pages:', ', '.join(built))
    print('redirects:', ', '.join(f'{o} -> {n}' for o, n in REDIRECTS.items()))
    for p in problems:
        print('PROBLEM', p)
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
