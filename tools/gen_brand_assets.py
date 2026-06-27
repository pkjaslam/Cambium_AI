#!/usr/bin/env python3
"""gen_brand_assets — recreate the Cambium brand asset set (SVG + PNG) from one source.
Motif: concentric emerald growth rings with a glowing lime 'active node' (BRAND.md, 'Living Layer')."""
import os, math, cairosvg

OUT = os.environ.get("BRAND_OUT", "/tmp/brandout")
os.makedirs(OUT, exist_ok=True)

# ---- palette ----
BG="#07231A"; PANEL="#0E3326"; PANEL2="#15402F"; LINE="#1F4D3B"
CANVAS="#F4F7F2"; INK="#0C1611"; MIST="#8AA197"
EMER="#16C079"; EMER_D="#0E8E5B"; LIME="#B7F36A"
FONT="Inter, 'DejaVu Sans', sans-serif"

def ring_mark(cx, cy, R, node_ang=52, rings=6, sw=None, sat=True):
    """Concentric emerald rings + lime active node + spoke. Returns SVG fragment."""
    sw = sw or R*0.016
    parts=[]
    # rings: outer faint -> inner bright
    for i in range(rings):
        r = R*(0.30 + 0.70*i/(rings-1))
        op = 0.30 + 0.62*(i/(rings-1))   # inner brighter
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="none" stroke="{EMER}" stroke-width="{sw*(1.05-0.04*i):.2f}" opacity="{op:.2f}"/>')
    # faint satellite nodes (the org) on a couple of rings
    if sat:
        for ang,fr,o in [(205,0.65,0.5),(310,0.86,0.42),(150,0.44,0.55)]:
            a=math.radians(ang); rr=R*fr
            parts.append(f'<circle cx="{cx+rr*math.cos(a):.1f}" cy="{cy+rr*math.sin(a):.1f}" r="{R*0.018:.2f}" fill="{EMER}" opacity="{o}"/>')
    # active node position (outer-ish ring)
    a=math.radians(node_ang); nr=R*0.86
    nx,ny=cx+nr*math.cos(a), cy+nr*math.sin(a)
    # spoke
    parts.append(f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="url(#spoke)" stroke-width="{sw*1.1:.2f}" stroke-linecap="round"/>')
    # node glow (layered) + core
    parts.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{R*0.20:.1f}" fill="url(#glow)"/>')
    parts.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{R*0.072:.1f}" fill="{LIME}"/>')
    parts.append(f'<circle cx="{nx-R*0.02:.1f}" cy="{ny-R*0.02:.1f}" r="{R*0.026:.1f}" fill="#EAFFC9"/>')
    # center
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{R*0.05:.1f}" fill="{EMER}"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{R*0.022:.1f}" fill="{LIME}"/>')
    return "\n".join(parts)

DEFS = f'''<defs>
  <radialGradient id="tile" cx="38%" cy="30%" r="85%">
    <stop offset="0%" stop-color="{PANEL2}"/><stop offset="55%" stop-color="{PANEL}"/><stop offset="100%" stop-color="{BG}"/>
  </radialGradient>
  <radialGradient id="glow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{LIME}" stop-opacity="0.95"/><stop offset="35%" stop-color="{LIME}" stop-opacity="0.45"/><stop offset="100%" stop-color="{LIME}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="spoke" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{EMER}" stop-opacity="0.5"/><stop offset="100%" stop-color="{LIME}" stop-opacity="0.95"/>
  </linearGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.10"/><stop offset="22%" stop-color="#FFFFFF" stop-opacity="0"/>
  </linearGradient>
</defs>'''

def icon_svg(S=200):
    pad=S*0.06; rad=S*0.225
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}">{DEFS}
  <rect x="{pad}" y="{pad}" width="{S-2*pad}" height="{S-2*pad}" rx="{rad}" fill="url(#tile)" stroke="{LINE}" stroke-width="{S*0.006}"/>
  <rect x="{pad}" y="{pad}" width="{S-2*pad}" height="{S-2*pad}" rx="{rad}" fill="url(#sheen)"/>
  {ring_mark(S/2, S/2, S*0.36)}
</svg>'''

def wordmark_svg(dark=False, W=820, H=200):
    txt = CANVAS if dark else INK
    sub = MIST
    m = ring_mark(118, H/2, 70)
    tile_rad=26
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">{DEFS}
  <g>
    <rect x="40" y="{H/2-78}" width="156" height="156" rx="{tile_rad}" fill="url(#tile)" stroke="{LINE}" stroke-width="1.2"/>
    <rect x="40" y="{H/2-78}" width="156" height="156" rx="{tile_rad}" fill="url(#sheen)"/>
    {m}
  </g>
  <text x="232" y="{H/2-2}" font-family="{FONT}" font-weight="800" font-size="80" letter-spacing="-3" fill="{txt}">Cambium<tspan fill="{LIME}">.</tspan></text>
  <text x="236" y="{H/2+44}" font-family="{FONT}" font-weight="500" font-size="23" letter-spacing="1.5" fill="{sub}">RESEARCH INSTITUTION · ONE SENTENCE</text>
</svg>'''

def social_svg(W=1280, H=640):
    # background node constellation (subtle org hint)
    import random; random.seed(7)
    nodes=[]
    for _ in range(26):
        x=random.uniform(60,W-60); y=random.uniform(50,H-50)
        nodes.append((x,y))
    edges=[]
    for i,(x,y) in enumerate(nodes):
        # connect to nearest 1
        best=None;bd=1e9
        for j,(x2,y2) in enumerate(nodes):
            if j==i:continue
            d=(x-x2)**2+(y-y2)**2
            if d<bd:bd=d;best=j
        if best is not None: edges.append((i,best))
    const=['<g opacity="0.10">']
    for i,j in edges:
        const.append(f'<line x1="{nodes[i][0]:.0f}" y1="{nodes[i][1]:.0f}" x2="{nodes[j][0]:.0f}" y2="{nodes[j][1]:.0f}" stroke="{EMER}" stroke-width="1"/>')
    for x,y in nodes:
        const.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="2.4" fill="{EMER}"/>')
    const.append('</g>')
    const="\n".join(const)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">{DEFS}
  <defs>
    <radialGradient id="bgmesh" cx="72%" cy="22%" r="80%">
      <stop offset="0%" stop-color="{PANEL2}"/><stop offset="48%" stop-color="{PANEL}"/><stop offset="100%" stop-color="{BG}"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="{H}" fill="url(#bgmesh)"/>
  {const}
  <rect x="20" y="20" width="{W-40}" height="{H-40}" rx="28" fill="none" stroke="{LINE}" stroke-width="1.5" opacity="0.8"/>
  <!-- mark tile -->
  <g>
    <rect x="96" y="232" width="184" height="184" rx="34" fill="url(#tile)" stroke="{LINE}" stroke-width="1.5"/>
    <rect x="96" y="232" width="184" height="184" rx="34" fill="url(#sheen)"/>
    {ring_mark(188, 324, 80)}
  </g>
  <text x="334" y="290" font-family="{FONT}" font-weight="800" font-size="118" letter-spacing="-4" fill="{CANVAS}">Cambium<tspan fill="{LIME}">.</tspan></text>
  <text x="338" y="356" font-family="{FONT}" font-weight="500" font-size="32" fill="{MIST}">A research institution you run with one sentence —</text>
  <text x="338" y="398" font-family="{FONT}" font-weight="500" font-size="32" fill="{MIST}">RFP to verified results, human-in-the-loop at every gate.</text>
  <g font-family="{FONT}" font-weight="700" font-size="33">
    <text x="338" y="470" fill="{EMER}">46<tspan fill="{CANVAS}" font-weight="600"> agents</tspan></text>
    <text x="520" y="470" fill="{MIST}" font-weight="400">·</text>
    <text x="548" y="470" fill="{EMER}">11<tspan fill="{CANVAS}" font-weight="600"> councils</tspan></text>
    <text x="760" y="470" fill="{MIST}" font-weight="400">·</text>
    <text x="788" y="470" fill="{LIME}">8<tspan fill="{CANVAS}" font-weight="600"> human gates</tspan></text>
  </g>
  <text x="338" y="540" font-family="{FONT}" font-weight="500" font-size="22" fill="{EMER_D}" letter-spacing="1">MIT · open source · runs in your Claude · the Cambium way</text>
</svg>'''

def favicon_svg(S=64):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}">{DEFS}
  <rect width="{S}" height="{S}" rx="{S*0.22}" fill="url(#tile)"/>
  {ring_mark(S/2,S/2,S*0.40, rings=4, sat=False)}
</svg>'''

def write(name, svg, png_sizes=None, vb=None):
    open(f"{OUT}/{name}.svg","w").write(svg)
    if png_sizes:
        for ps in png_sizes:
            suf = "" if len(png_sizes)==1 else f"@{ps}"
            cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{OUT}/{name}{suf}.png", output_width=ps, output_height=int(ps*(vb[1]/vb[0])) if vb else ps)

# build
write("logo-mark", icon_svg(200), png_sizes=[512,1024], vb=(200,200))
write("logo", wordmark_svg(False), png_sizes=[1560], vb=(780,200))
write("logo-dark", wordmark_svg(True), png_sizes=[1560], vb=(780,200))
write("social-preview", social_svg(), png_sizes=[1280], vb=(1280,640))
write("favicon", favicon_svg(64), png_sizes=[64,180], vb=(64,64))
print("generated:", sorted(os.listdir(OUT)))
