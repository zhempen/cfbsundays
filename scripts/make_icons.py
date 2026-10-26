"""Makes the site icons: site/favicon.svg and site/icon-180.png.
The mark is a goalpost in front of a gold sunset with retro horizon stripes:
football, on Sundays. No team, league or trophy shapes (colors-only rule).
Run: pip install playwright; python scripts/make_icons.py
"""
NAVY = '#0e1830'; GOLD = '#ffc629'; POST = '#ffffff'


def post(w=5.5, top=8, bar=29, l=15, r=49, base=58):
    h = w / 2
    return (f'<path fill="{POST}" d="M{l-h} {top}h{w}V{bar-h}H{r-h}V{top}h{w}V{bar+h}'
            f'H{32+h}V{base}h-{w}V{bar+h}H{l-h}Z"/>')


def mark(rounded=True):
    rx = ' rx="12"' if rounded else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64"{rx} fill="{NAVY}"/>
<clipPath id="h"><path d="M0 0H64V44H0Z"/></clipPath>
<g clip-path="url(#h)"><circle cx="32" cy="42" r="22" fill="{GOLD}"/>
<rect y="33" width="64" height="2.2" fill="{NAVY}"/><rect y="38.5" width="64" height="2.6" fill="{NAVY}"/></g>
{post()}
</svg>
'''


if __name__ == '__main__':
    open('site/favicon.svg', 'w').write(mark())
    from playwright.sync_api import sync_playwright
    svg = mark(rounded=False).replace('<svg ', '<svg width="180" height="180" ', 1)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 180, 'height': 180})
        pg.set_content(f'<body style="margin:0">{svg}</body>')
        pg.screenshot(path='site/icon-180.png', clip={'x': 0, 'y': 0, 'width': 180, 'height': 180}); b.close()
