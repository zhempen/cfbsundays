"""Makes the site icons from Saira (OFL, site/fonts): site/favicon.svg and site/icon-180.png.
The mark is the gold selection bar with a chrome leading stripe and "CFB" in Saira 900 italic.
Run: pip install fonttools brotli playwright; python scripts/make_icons.py
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
def text_path(txt,wght,wdth,track=0):
    inst=instantiateVariableFont(TTFont('site/fonts/saira-latin-var-italic.woff2'),{'wght':wght,'wdth':wdth})
    gs=inst.getGlyphSet();cmap=inst.getBestCmap();hm=inst['hmtx']
    bp=BoundsPen(gs);x=0;parts=[]
    for ch in txt:
        g=cmap[ord(ch)];parts.append((g,x));x+=hm[g][0]+track
    for g,x0 in parts:
        gs[g].draw(TransformPen(bp,(1,0,0,1,x0,0)))
    return inst,gs,parts,bp.bounds
def place(txt,wght,wdth,box,track=0):
    inst,gs,parts,(x0,y0,x1,y1)=text_path(txt,wght,wdth,track)
    bx,by,bw,bh=box
    s=min(bw/(x1-x0),bh/(y1-y0))
    w=(x1-x0)*s;h=(y1-y0)*s
    ox=bx+(bw-w)/2-x0*s; oy=by+(bh-h)/2+y1*s
    sp=SVGPathPen(gs)
    for g,xo in parts:
        gs[g].draw(TransformPen(sp,(s,0,0,-s,ox+xo*s,oy)))
    return sp.getCommands()
NAVY='#0e1830';GOLD='#ffc629';INK='#0e1830'
def B2():
    d=place('CFB',900,78,(13.5,15,41,34),track=16)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<path d="M16 5H64L48 59H0Z" fill="{GOLD}"/>
<path d="M16 5H24L8 59H0Z" fill="#c3c9d2"/>
<path fill="{INK}" d="{d}"/>
</svg>'''
def T():
    d=place('CFB',900,78,(15,21,38,22),track=16)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" fill="{NAVY}"/>
<path d="M18 14H58L48 50H8Z" fill="{GOLD}"/>
<path d="M18 14H23.5L13.5 50H8Z" fill="#c3c9d2"/>
<path d="M23.5 14H58L57.6 15.5H23.1Z" fill="#fff" opacity=".5"/>
<path fill="{INK}" d="{d}"/>
</svg>'''

if __name__=='__main__':
    open('site/favicon.svg','w').write(B2())
    from playwright.sync_api import sync_playwright
    svg=T().replace('<svg ','<svg width="180" height="180" ',1)
    with sync_playwright() as p:
        b=p.chromium.launch();pg=b.new_page(viewport={'width':180,'height':180})
        pg.set_content(f'<body style="margin:0">{svg}</body>')
        pg.screenshot(path='site/icon-180.png',clip={'x':0,'y':0,'width':180,'height':180});b.close()
