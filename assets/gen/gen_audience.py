#!/usr/bin/env python3
"""Generate assets/audience.svg - the "who it's for" map (five audiences, one institute).
Usage: python3 assets/gen/gen_audience.py
Brand palette matches assets/gen/gen_hero.py.
"""
import os, math
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H = 1240, 466
FONT = "Inter, 'DejaVu Sans', Arial, sans-serif"
BG="#07231A"; PANEL="#0E3326"; PANEL2="#15402F"; HAIR="#1F4D3B"
CANVAS="#F4F7F2"; MUTED="#8AA197"; EMER="#16C079"; EMERD="#0E8E5B"; LIME="#B7F36A"

def hexpts(cx, cy, r):
    return " ".join(f"{cx+r*math.cos(math.radians(60*i-90)):.1f},{cy+r*math.sin(math.radians(60*i-90)):.1f}" for i in range(6))

def esc(t):
    return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# five audiences: (title lines, value lines, source tag, accent)
CARDS = [
    (["RESEARCHERS", "& PIs"],
     ["Run a project end to end,", "from RFP to publish,", "a human at every gate."],
     "46 agents · 8 gates", LIME),
    (["RESEARCH ADMIN", "& SPONSORED PROGRAMS"],
     ["Pre-award drafting,", "budget-to-solicitation review,", "an AI-use disclosure builder."],
     "ai_disclosure · budget_review", EMER),
    (["DEVELOPERS", "& CONTRIBUTORS"],
     ["A plugin with an MCP server,", "a 121-tool stdlib kit,", "tests, clean extension points."],
     "MCP · pytest · skills", LIME),
    (["INSTITUTIONS", "& FUNDERS"],
     ["MIT, local-first,", "data-sovereign; every gate", "logged in plain markdown."],
     "GATES.md · auditable", EMER),
    (["EDUCATORS", "& LEARNERS"],
     ["The Academy: ten modules,", "three tiers, plus a", "Learning Lab every run."],
     "academy · learning gate", LIME),
]

s=[]
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="Who Cambium is for: one governed institute, five audiences - researchers and PIs, research administrators and sponsored programs, developers and contributors, institutions and funders, and educators and learners.">')
s.append('<defs>')
s.append(f'<linearGradient id="bgg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#07231A"/><stop offset="100%" stop-color="#0A2A1F"/></linearGradient>')
s.append(f'<linearGradient id="hexg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{LIME}"/><stop offset="100%" stop-color="{EMER}"/></linearGradient>')
s.append(f'<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{LIME}" stop-opacity="0.25"/><stop offset="100%" stop-color="{LIME}" stop-opacity="0"/></radialGradient>')
s.append('</defs>')
s.append(f'<rect width="{W}" height="{H}" fill="url(#bgg)"/>')

# faint tree-ring arcs, bottom-right
rcx, rcy = 1160, 300
for i,r in enumerate(range(80, 560, 40)):
    col = EMER if i%2==0 else EMERD
    s.append(f'<circle cx="{rcx}" cy="{rcy}" r="{r}" fill="none" stroke="{col}" stroke-width="1.3" opacity="{0.05+(i%3)*0.015:.3f}"/>')

# header: hex mark + title
hx, hy, hr = 62, 60, 30
s.append(f'<circle cx="{hx}" cy="{hy}" r="52" fill="url(#glow)"/>')
s.append(f'<polygon points="{hexpts(hx,hy,hr)}" fill="none" stroke="url(#hexg)" stroke-width="4" stroke-linejoin="round"/>')
for r in (7,15,23):
    s.append(f'<circle cx="{hx}" cy="{hy}" r="{r}" fill="none" stroke="{EMER}" stroke-width="1.2" opacity="0.5"/>')
s.append(f'<circle cx="{hx}" cy="{hy}" r="4" fill="{LIME}"/>')
s.append(f'<text x="108" y="52" fill="{CANVAS}" font-size="30" font-weight="800" letter-spacing="1">WHO IT’S FOR</text>')
s.append(f'<text x="110" y="80" fill="{EMER}" font-size="16" font-weight="600" letter-spacing="0.5">One governed institute. Five ways in. The volume is the machine’s; the judgment stays yours.</text>')
s.append(f'<line x1="30" y1="104" x2="{W-30}" y2="104" stroke="{HAIR}" stroke-width="1.3"/>')

# five cards
margin, gap = 30, 16
cw = (W - 2*margin - 4*gap) / 5
cy0, ch = 124, 316
for i,(title, vals, tag, accent) in enumerate(CARDS):
    x = margin + i*(cw+gap)
    s.append(f'<rect x="{x:.0f}" y="{cy0}" width="{cw:.0f}" height="{ch}" rx="12" fill="{PANEL}" stroke="{HAIR}" stroke-width="1.3"/>')
    s.append(f'<rect x="{x:.0f}" y="{cy0}" width="{cw:.0f}" height="6" rx="3" fill="{accent}"/>')
    # number chip
    s.append(f'<circle cx="{x+26:.0f}" cy="{cy0+38}" r="15" fill="{PANEL2}" stroke="{accent}" stroke-width="1.4"/>')
    s.append(f'<text x="{x+26:.0f}" y="{cy0+43}" text-anchor="middle" fill="{accent}" font-size="15" font-weight="800">{i+1}</text>')
    # title (up to 2 lines)
    ty = cy0+78
    for ln in title:
        s.append(f'<text x="{x+18:.0f}" y="{ty}" fill="{CANVAS}" font-size="14" font-weight="800" letter-spacing="0">{esc(ln)}</text>')
        ty += 21
    # value lines
    vy = ty + 12
    for ln in vals:
        s.append(f'<text x="{x+18:.0f}" y="{vy}" fill="{MUTED}" font-size="13" font-weight="500">{esc(ln)}</text>')
        vy += 20
    # source tag (mono) pinned near bottom
    s.append(f'<text x="{x+18:.0f}" y="{cy0+ch-18}" fill="{EMERD}" font-size="10.5" font-weight="600" font-family="ui-monospace, monospace">{esc(tag)}</text>')

s.append(f'<text x="{W-30}" y="{H-14}" text-anchor="end" fill="{MUTED}" font-size="12" font-weight="500">MIT · local-first · human-in-the-loop at every gate</text>')
s.append('</svg>')
open(os.path.join(ROOT,"assets","audience.svg"),"w").write("\n".join(s))
print("[gen_audience] wrote assets/audience.svg")
