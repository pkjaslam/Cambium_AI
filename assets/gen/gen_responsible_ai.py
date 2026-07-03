#!/usr/bin/env python3
"""Generate assets/responsible-ai.svg - every AI-in-research risk, its Cambium control,
and HOW HARD the control actually bites (honest enforcement tier) + the real source file.
Usage: python3 assets/gen/gen_responsible_ai.py
"""
import os, math
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W = 1120
FONT = "Inter, 'DejaVu Sans', Arial, sans-serif"
BG="#07231A"; PANEL="#0E3326"; PANEL2="#15402F"; HAIR="#1F4D3B"
CANVAS="#F4F7F2"; MUTED="#8AA197"; DIM="#6E877B"; EMER="#16C079"; EMERD="#0E8E5B"
LIME="#B7F36A"; AMBER="#E8B84B"; RISK="#E58A8A"; RISKBD="#7d3b3b"

def esc(t): return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# tier: A = CI blocks the build, B = gate-enforced (token/run-checked), C = required check before the gate
TIERS = {"A": (LIME,  "CI blocks the build"),
         "B": (EMER,  "gate-enforced, token-checked"),
         "C": (AMBER, "required check before the gate")}

# (risk title, risk sub, control name, mechanism, tier, source file)
ROWS = [
 ("Overclaiming", "stating more than the evidence supports",
  "Four-tier evidence contract", "validate.py fails the build on any claim past its evidence tier",
  "A", "governance/validate.py"),
 ("Fabricated or unresolvable citations", "references that do not exist",
  "Citation resolution", "unresolved or unsupported = release blocker; DOIs checked at Crossref / doi.org",
  "A", "validate.py · paper_search.py"),
 ("Speed collapses human judgment", "decisions outrun deliberation",
  "Pace check", "a deliberation interval between gates, enforced in the gauntlet",
  "B", "tools/pace_check.py"),
 ("AI erases the human's learning", "you ship work you did not grow into",
  "Learning Gate", "a run cannot close until it delivers a learning packet",
  "B", "tools/learning_delivery.py"),
 ("Authorship and accountability blur", "no one is responsible",
  "Named signature at every gate", "a person's approval token is required and logged; AI is never an author",
  "B", "gate_lock.py · GATES.md"),
 ("Bias goes unexamined", "unfairness ships unchecked",
  "Bias checklist (NIST AI RMF)", "a required checklist completed before the results gates",
  "C", "templates/BIAS_MITIGATION_CHECKLIST.md"),
 ("Sensitive data leaks", "PII or regulated data escapes",
  "PII / regulated-data scan", "scans for sensitive data in your own account before release",
  "C", "tools/pii_screen.py"),
]

rowh, gap, top = 78, 6, 128
H = top + len(ROWS)*(rowh+gap) + 96

s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="Every risk of AI in research mapped to a Cambium control and how hard the control is enforced, with the real source file for each.">']
s.append(f'<defs><linearGradient id="bgg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#07231A"/><stop offset="100%" stop-color="#0A2A1F"/></linearGradient>')
s.append(f'<marker id="arw" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z" fill="{EMER}"/></marker></defs>')
s.append(f'<rect width="{W}" height="{H}" fill="url(#bgg)"/>')
# faint tree rings, bottom-right
rcx, rcy = W-40, H-40
for i,r in enumerate(range(80, 560, 42)):
    s.append(f'<circle cx="{rcx}" cy="{rcy}" r="{r}" fill="none" stroke="{EMER if i%2==0 else EMERD}" stroke-width="1.2" opacity="{0.05+(i%3)*0.014:.3f}"/>')
# header
s.append(f'<text x="40" y="46" fill="{CANVAS}" font-size="27" font-weight="800">Every risk, its control, and how hard the control bites</text>')
s.append(f'<text x="40" y="74" fill="{MUTED}" font-size="14">Most tools answer AI risk with a policy page. Cambium wires each risk to something that runs. Where a control is softer, this diagram says so.</text>')
# column captions
s.append(f'<text x="44" y="112" fill="{RISK}" font-size="12" font-weight="700" letter-spacing="1.5">THE RISK</text>')
s.append(f'<text x="476" y="112" fill="{EMER}" font-size="12" font-weight="700" letter-spacing="1.5">THE CONTROL, AND HOW HARD IT BITES</text>')

rx, rw = 40, 372
cx, cw = 476, 604
for i,(rt, rs, cn, mech, tier, src) in enumerate(ROWS):
    y = top + i*(rowh+gap)
    mid = y + rowh/2
    tcol, tlab = TIERS[tier]
    # risk card
    s.append(f'<rect x="{rx}" y="{y}" width="{rw}" height="{rowh}" rx="11" fill="{PANEL}" stroke="{RISKBD}" stroke-width="1.4"/>')
    s.append(f'<rect x="{rx}" y="{y}" width="5" height="{rowh}" rx="2.5" fill="{RISK}"/>')
    s.append(f'<text x="{rx+20}" y="{y+31}" fill="{CANVAS}" font-size="15.5" font-weight="700">{esc(rt)}</text>')
    s.append(f'<text x="{rx+20}" y="{y+53}" fill="{MUTED}" font-size="12">{esc(rs)}</text>')
    # arrow
    s.append(f'<line x1="{rx+rw+10}" y1="{mid}" x2="{cx-12}" y2="{mid}" stroke="{EMER}" stroke-width="2" marker-end="url(#arw)"/>')
    # control card
    s.append(f'<rect x="{cx}" y="{y}" width="{cw}" height="{rowh}" rx="11" fill="{PANEL}" stroke="{HAIR}" stroke-width="1.4"/>')
    s.append(f'<rect x="{cx}" y="{y}" width="5" height="{rowh}" rx="2.5" fill="{tcol}"/>')
    s.append(f'<text x="{cx+20}" y="{y+27}" fill="{tcol}" font-size="15.5" font-weight="800">{esc(cn)}</text>')
    # tier chip (top-right)
    chipw = len(tlab)*6.4 + 20
    s.append(f'<rect x="{cx+cw-chipw-14:.0f}" y="{y+11}" width="{chipw:.0f}" height="20" rx="10" fill="none" stroke="{tcol}" stroke-width="1.3"/>')
    s.append(f'<text x="{cx+cw-chipw/2-14:.0f}" y="{y+25}" text-anchor="middle" fill="{tcol}" font-size="10.5" font-weight="700">{esc(tlab)}</text>')
    s.append(f'<text x="{cx+20}" y="{y+48}" fill="{MUTED}" font-size="12">{esc(mech)}</text>')
    s.append(f'<text x="{cx+20}" y="{y+67}" fill="{EMERD}" font-size="11" font-weight="600" font-family="ui-monospace, monospace">{esc(src)}</text>')

# legend
ly = top + len(ROWS)*(rowh+gap) + 8
s.append(f'<text x="40" y="{ly+4}" fill="{DIM}" font-size="11.5" font-weight="600">HOW HARD IT BITES:</text>')
lx = 190
for k in ("A","B","C"):
    col, lab = TIERS[k]
    s.append(f'<rect x="{lx}" y="{ly-10}" width="14" height="14" rx="3" fill="{col}"/>')
    s.append(f'<text x="{lx+21}" y="{ly+2}" fill="{MUTED}" font-size="12">{esc(lab)}</text>')
    lx += 40 + len(lab)*6.6
# footer bar
fy = ly + 26
s.append(f'<rect x="40" y="{fy}" width="{W-80}" height="34" rx="10" fill="{LIME}"/>')
s.append(f'<text x="{W/2:.0f}" y="{fy+22}" text-anchor="middle" fill="#0a2a1f" font-size="14" font-weight="700">The human stays responsible for validity, ethics, and decisions.</text>')
s.append('</svg>')
open(os.path.join(ROOT,"assets","responsible-ai.svg"),"w").write("\n".join(s))
print("[gen_responsible_ai] wrote assets/responsible-ai.svg  (H=%d)"%H)
