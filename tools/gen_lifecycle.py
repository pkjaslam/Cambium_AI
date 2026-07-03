#!/usr/bin/env python3
"""
gen_lifecycle.py - emit assets/lifecycle.svg

The eight phases of a Cambium run: the councils that act in each, the human
gate that closes each, and WHAT THE PERSON ACTUALLY DECIDES at that gate.
G4 is marked because results are accepted only after every number is reproduced.
Structure lives in PHASES, so the picture stays a faithful map of the workflow.

Run:  python3 tools/gen_lifecycle.py   (no third-party dependencies)
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "lifecycle.svg")

BG="#07231A"; INK="#F4F7F2"; MUTED="#8AA197"; DIM="#6f8a7e"
PANEL="#0E3326"; LINE="#1F4D3B"; LIME="#B7F36A"; GOLD="#E0B24A"; GREEN="#16C079"
HUE = {"Orchestration":"#7C5CFF","Pre-Award":"#2BB8C4","Scouts":"#19C0A6","Labs":"#3D8BFF",
       "Verification":"#FF6B5E","Execution":"#16C079","Reporting":"#E0B24A","Support":"#E08A4A","Governance":"#9B8CFF"}

# name, subtitle, gate id, decide(question), director-only?, councils, reproduce-marker?
PHASES = [
 ("Intake",         "know the PI and RFP", "G0",  "worth our time?",    False, ["Orchestration","Support"], False),
 ("Pre-Award",      "ideas, team, aims",   "G1",  "pursue this?",       False, ["Pre-Award","Scouts"],      False),
 ("Design",         "approach, budget",    "G2",  "which approach?",    False, ["Pre-Award","Labs"],        False),
 ("Submit",         "proposal final",      "G3",  "finalize & submit",  True,  ["Governance","Orchestration"], False),
 ("Build / Run-Lab","run the work",        "G3a", "budget + compliance",False, ["Labs","Execution"],        False),
 ("Verify",         "reproduce numbers",   "G4",  "accept results",     False, ["Verification"],            True),
 ("Report",         "findings, deck",      "G5",  "release report?",    False, ["Reporting","Support"],     False),
 ("Publish",        "release, closeout",   "G6",  "go public?",         False, ["Governance","Reporting"],  False),
]

W, H = 1120, 470
LEFT, RIGHT = 40, 1080
COL = (RIGHT-LEFT)/len(PHASES)
CENTERS = [int(LEFT + COL/2 + i*COL) for i in range(len(PHASES))]

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def build():
    p=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
       f'font-family="Inter,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif" role="img" '
       f'aria-label="The Cambium research lifecycle: eight phases, each showing the councils that act in it, '
       f'the human gate that closes it, and what the person decides at that gate. Results at G4 are accepted only '
       f'after every number is reproduced. A named person signs every gate.">']
    p.append('<defs>')
    p.append('<linearGradient id="lbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#0b2c20"/><stop offset="100%" stop-color="#07231a"/></linearGradient>')
    p.append('<linearGradient id="flow" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#16C079"/><stop offset="100%" stop-color="#B7F36A"/></linearGradient>')
    p.append('</defs>')
    p.append(f'<rect width="{W}" height="{H}" rx="18" fill="url(#lbg)"/>')
    p.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="17" fill="none" stroke="{LINE}"/>')
    p.append(f'<text x="40" y="44" font-size="25" font-weight="800" fill="{INK}">The Cambium research lifecycle</text>')
    p.append(f'<text x="40" y="69" font-size="13.5" fill="{MUTED}">Eight phases, eight human gates. A named person signs each one, and this is what they decide.</text>')

    # phase blocks
    for i,(name,sub,*_r) in enumerate(PHASES):
        c=CENTERS[i]; x=c-58
        p.append(f'<rect x="{x}" y="92" width="116" height="70" rx="12" fill="{PANEL}" stroke="{LINE}"/>')
        p.append(f'<text x="{c}" y="125" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}">{esc(name)}</text>')
        p.append(f'<text x="{c}" y="144" text-anchor="middle" font-size="9.5" fill="{MUTED}">{esc(sub)}</text>')
        if i<len(PHASES)-1:
            midx=(CENTERS[i]+CENTERS[i+1])/2
            p.append(f'<text x="{midx}" y="134" text-anchor="middle" font-size="17" fill="{GREEN}">&#8250;</text>')

    # flow line
    p.append(f'<line x1="{LEFT}" y1="200" x2="{RIGHT}" y2="200" stroke="url(#flow)" stroke-width="5" stroke-linecap="round"/>')

    # gate badges + decision
    for i,(_n,_s,gid,decide,director,_co,repro) in enumerate(PHASES):
        c=CENTERS[i]
        fill = GOLD if director else (GREEN if repro else LIME)
        stroke = "#9C7A1E" if director else ("#0B3325" if repro else "#0B2E22")
        p.append(f'<rect x="{c-25}" y="188" width="50" height="24" rx="7" fill="{fill}" stroke="{stroke}"/>')
        p.append(f'<text x="{c}" y="204" text-anchor="middle" font-size="11" font-weight="800" fill="#062013">{esc(gid)}</text>')
        p.append(f'<text x="{c}" y="234" text-anchor="middle" font-size="11" font-weight="700" fill="{INK}">{esc(decide)}</text>')
        if director:
            p.append(f'<text x="{c}" y="249" text-anchor="middle" font-size="9" font-weight="700" fill="{GOLD}">Director only</text>')
        if repro:
            p.append(f'<rect x="{c-52}" y="242" width="104" height="17" rx="8.5" fill="none" stroke="{GREEN}" stroke-width="1.1"/>')
            p.append(f'<text x="{c}" y="254" text-anchor="middle" font-size="8.7" font-weight="700" fill="{GREEN}">every number reproduced</text>')

    # council band
    p.append(f'<text x="40" y="298" font-size="10" letter-spacing="1.5" fill="{MUTED}">WHO ACTS IN EACH PHASE</text>')
    for i,(_n,_s,_g,_d,_dir,councils,_r) in enumerate(PHASES):
        c=CENTERS[i]; n=len(councils); ys=[318] if n==1 else [310,336]
        for j,council in enumerate(councils):
            hue=HUE[council]; y=ys[j]
            p.append(f'<rect x="{c-56}" y="{y}" width="112" height="22" rx="11" fill="{hue}" fill-opacity="0.15" stroke="{hue}" stroke-opacity="0.6"/>')
            p.append(f'<text x="{c}" y="{y+15}" text-anchor="middle" font-size="9.5" font-weight="700" fill="{hue}">{esc(council)}</text>')

    # legend
    ly=392
    p.append(f'<rect x="40" y="{ly-12}" width="16" height="14" rx="4" fill="{LIME}"/><text x="62" y="{ly}" font-size="11.5" fill="{MUTED}">human gate</text>')
    p.append(f'<rect x="176" y="{ly-12}" width="16" height="14" rx="4" fill="{GOLD}"/><text x="198" y="{ly}" font-size="11.5" fill="{MUTED}">Director-only gate</text>')
    p.append(f'<rect x="348" y="{ly-12}" width="16" height="14" rx="4" fill="{GREEN}"/><text x="370" y="{ly}" font-size="11.5" fill="{MUTED}">results reproduced before accepted</text>')
    p.append(f'<rect x="628" y="{ly-12}" width="16" height="14" rx="7" fill="{HUE["Scouts"]}" fill-opacity="0.2" stroke="{HUE["Scouts"]}"/><text x="650" y="{ly}" font-size="11.5" fill="{MUTED}">council acting in this phase</text>')

    p.append(f'<text x="40" y="{H-20}" font-size="11" fill="{DIM}">Gates are prompt-level and token-checked, not a hard OS lock. The point is that a person decides at each one.</text>')
    p.append('</svg>')
    return "\n".join(p)

def main():
    svg=build()
    open(OUT,"w",encoding="utf-8").write(svg)
    assert chr(0x2014) not in svg, "em dash found"
    print(f"[gen_lifecycle] wrote {os.path.relpath(OUT,ROOT)} ({len(PHASES)} phases)")

if __name__=="__main__": main()
