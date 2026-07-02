#!/usr/bin/env python3
"""
gen_runboard_gif.py - build assets/run_board.gif

A short looping animation of one Cambium run, in the readable board style that
matches the live v1.39 in-chat board: started councils show their agents with a
one-line finding as each reports, not-yet-started councils collapse into a single
"Up next" strip, and the human gate card leads with the Approve / Revise / Reject
decision bar. The numbers shown are illustrative, not from a real study, and every
frame says so.

Standalone. Run by hand when you want to refresh the asset:
    python3 assets/gen/gen_runboard_gif.py

Deps: Pillow >= 9.0, imageio >= 2.28,<3.
"""
import os
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "run_board.gif")

W, H = 760, 540

BG = (7, 35, 26)
PANEL = (14, 51, 38)
CARD = (16, 57, 42)
LINE = (31, 77, 59)
INK = (244, 247, 242)
MUT = (138, 161, 151)
DIM = (111, 138, 126)
GREEN = (22, 192, 121)
LIME = (183, 243, 106)
GOLD = (224, 178, 74)
RED = (255, 107, 94)
QUEUED = (58, 110, 87)

SCOUTS = (25, 192, 166)
LABS = (61, 139, 255)
VERIFY = (255, 107, 94)

FONTDIR = "/usr/share/fonts/truetype/dejavu/"


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(os.path.join(FONTDIR, name), size)
    except Exception:
        return ImageFont.load_default()


F_TITLE = font(18, True)
F_SUB = font(12)
F_PHASE = font(12, True)
F_NAME = font(14, True)
F_FIND = font(11)
F_TAG = font(11, True)
F_GATE = font(15, True)
F_GATEBIG = font(19, True)
F_GMID = font(12)
F_BTN = font(12, True)
F_FOOT = font(10)
F_BANNER = font(15, True)
F_UP = font(12, True)

AGENTS = [
    ("scout-prior-art", "Scouts",       "novelty distance 0.41, prior art mapped"),
    ("scout-landscape", "Scouts",       "12 efforts, 3 open datasets located"),
    ("lab-methods",     "Labs",         "method drafted, controls in place"),
    ("lab-statistics",  "Labs",         "power 0.86, intervals computed"),
    ("verify-evidence", "Verification", "every headline number reproduced"),
    ("referee",         "Verification", "accept with minor revisions"),
]

COUNCIL_ORDER = []
for _n, _c, _f in AGENTS:
    if _c not in COUNCIL_ORDER:
        COUNCIL_ORDER.append(_c)
COUNCIL_COUNT = {c: sum(1 for _n, cc, _f in AGENTS if cc == c) for c in COUNCIL_ORDER}

FRAMES = [
    dict(p=0.00, phase=("PHASE 1 - SCOUTS", SCOUTS),
         st="qqqqqq", started={"Scouts"}, gate=None, dur=1.5),
    dict(p=0.17, phase=("PHASE 1 - SCOUTS", SCOUTS),
         st="wqqqqq", started={"Scouts"}, gate=None, dur=1.3),
    dict(p=0.42, phase=("PHASE 2 - LABS", LABS),
         st="ddwqqq", started={"Scouts", "Labs"}, gate=None, dur=1.7),
    dict(p=0.67, phase=("PHASE 3 - VERIFICATION", VERIFY),
         st="ddddwq", started={"Scouts", "Labs", "Verification"}, gate=None, dur=1.5),
    dict(p=0.83, phase=("HUMAN GATE", GOLD),
         st="dddddd", started={"Scouts", "Labs", "Verification"}, gate="ask", dur=2.1),
    dict(p=0.92, phase=("HUMAN GATE", GREEN),
         st="dddddd", started={"Scouts", "Labs", "Verification"}, gate="approved", dur=1.6),
    dict(p=1.00, phase=("COMPLETE", GREEN),
         st="dddddd", started={"Scouts", "Labs", "Verification"}, gate=None, banner=True, dur=2.1),
]


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def center_text(d, cx, y, text, fnt, fill):
    w = d.textlength(text, font=fnt)
    d.text((cx - w / 2, y), text, font=fnt, fill=fill)


def draw_frame(spec):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    rrect(d, (1, 1, W - 2, H - 2), 16, outline=LINE, width=1)

    d.regular_polygon((42, 36, 13), 6, rotation=90, fill=GREEN)
    d.text((64, 18), "CAMBIUM INSTITUTE", font=F_TITLE, fill=INK)
    d.text((64, 42), "run board   -   research run: add math + stats + ML skills", font=F_SUB, fill=MUT)

    label, lcol = spec["phase"]
    lw = d.textlength(label, font=F_PHASE)
    tint = tuple(int(c * 0.18 + b * 0.82) for c, b in zip(lcol, BG))
    rrect(d, (W - 30 - lw - 22, 22, W - 30, 46), 12, fill=tint, outline=lcol, width=1)
    d.text((W - 30 - lw - 11, 28), label, font=F_PHASE, fill=lcol)

    bx0, bx1, by = 30, W - 70, 78
    rrect(d, (bx0, by, bx1, by + 12), 6, fill=PANEL, outline=LINE, width=1)
    fillw = int((bx1 - bx0) * spec["p"])
    if fillw > 6:
        rrect(d, (bx0, by, bx0 + fillw, by + 12), 6, fill=GREEN)
    d.text((bx1 + 14, by - 1), f"{int(spec['p']*100)}%", font=F_TAG, fill=MUT)

    started = spec.get("started", set())
    top = 108
    rh = 56
    row = 0
    for i, (name, council, finding) in enumerate(AGENTS):
        if council not in started:
            continue
        s = spec["st"][i]
        y = top + row * rh
        row += 1
        rrect(d, (30, y, W - 30, y + rh - 8), 10, fill=PANEL, outline=LINE, width=1)
        dot = {"q": QUEUED, "w": GOLD, "d": GREEN}[s]
        cx, cy = 50, y + (rh - 8) / 2
        if s == "w":
            d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), outline=GOLD, width=2)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=dot)
        nm_col = INK if s != "q" else MUT
        d.text((74, y + 9), name, font=F_NAME, fill=nm_col)
        d.text((74 + d.textlength(name, font=F_NAME) + 12, y + 12), council, font=F_FIND, fill=DIM)
        if s == "d":
            d.text((74, y + 28), finding, font=F_FIND, fill=MUT)
        elif s == "w":
            d.text((74, y + 28), "running ...", font=F_FIND, fill=GOLD)
        tag = {"q": ("queued", MUT), "w": ("working", GOLD), "d": ("done", GREEN)}[s]
        ttxt = "done" if s == "d" else tag[0]
        tw = d.textlength(ttxt, font=F_TAG)
        if s == "d":
            d.line((W - 44 - tw - 14, y + 22, W - 44 - tw - 9, y + 27), fill=GREEN, width=2)
            d.line((W - 44 - tw - 9, y + 27, W - 44 - tw - 2, y + 17), fill=GREEN, width=2)
        d.text((W - 44 - tw, y + 16), ttxt, font=F_TAG, fill=tag[1])

    upnext = [c for c in COUNCIL_ORDER if c not in started]
    if upnext and not spec.get("gate") and not spec.get("banner"):
        y = top + row * rh + 2
        rrect(d, (30, y, W - 30, y + 30), 9, fill=(10, 39, 29), outline=LINE, width=1)
        d.text((44, y + 8), "Up next", font=F_UP, fill=MUT)
        x = 44 + d.textlength("Up next", font=F_UP) + 16
        for j, c in enumerate(upnext):
            chip = f"{c} ({COUNCIL_COUNT[c]})"
            d.ellipse((x, y + 11, x + 7, y + 18), outline=DIM, width=1)
            d.text((x + 13, y + 8), chip, font=F_FIND, fill=INK)
            x += 13 + d.textlength(chip, font=F_FIND) + 16
            if j < len(upnext) - 1:
                d.text((x - 12, y + 7), "->", font=F_FIND, fill=DIM)

    gate = spec.get("gate")
    if gate:
        gw, gh = 490, 158
        gx, gy = (W - gw) // 2, 190
        rrect(d, (gx + 4, gy + 5, gx + gw + 4, gy + gh + 5), 14, fill=(4, 22, 16))
        border = GREEN if gate == "approved" else LIME
        rrect(d, (gx, gy, gx + gw, gy + gh), 14, fill=CARD, outline=border, width=2)
        sx = gx + 26
        if gate == "ask":
            d.rounded_rectangle((sx, gy + 18, sx + 14, gy + 34), radius=4, fill=LIME)
            d.text((sx + 24, gy + 16), "GATE G4   -   accept results?", font=F_GATE, fill=INK)
            by0 = gy + 44
            b1 = (sx, by0, sx + 132, by0 + 34)
            rrect(d, b1, 9, fill=GREEN)
            center_text(d, (b1[0] + b1[2]) / 2, by0 + 9, "APPROVE", F_BTN, (5, 32, 21))
            b2 = (sx + 148, by0, sx + 258, by0 + 34)
            rrect(d, b2, 9, fill=CARD, outline=GOLD, width=1)
            center_text(d, (b2[0] + b2[2]) / 2, by0 + 9, "REVISE", F_BTN, GOLD)
            b3 = (sx + 274, by0, sx + 384, by0 + 34)
            rrect(d, b3, 9, fill=CARD, outline=RED, width=1)
            center_text(d, (b3[0] + b3[2]) / 2, by0 + 9, "REJECT", F_BTN, RED)
            d.text((sx, gy + 92), "your decision. nothing finalizes without APPROVE.",
                   font=F_GMID, fill=MUT)
            d.text((sx, gy + 116), "evidence: referee accept   -   every number reproduced",
                   font=F_FIND, fill=DIM)
        else:
            d.rounded_rectangle((sx, gy + 34, sx + 16, gy + 52), radius=4, fill=LIME)
            d.text((sx + 26, gy + 30), "G4 APPROVED", font=F_GATEBIG, fill=GREEN)
            d.text((sx, gy + 70), "results accepted. proceeding to report.",
                   font=F_GMID, fill=MUT)
            d.text((sx, gy + 98), "the Director signed. the run continues.",
                   font=F_FIND, fill=DIM)

    if spec.get("banner"):
        bx, byy, bw, bh = 30, 300, W - 60, 70
        rrect(d, (bx, byy, bx + bw, byy + bh), 12, fill=(16, 57, 42), outline=GREEN, width=2)
        center_text(d, W / 2, byy + 16, "run complete", F_BANNER, LIME)
        center_text(d, W / 2, byy + 42, "every number reproduced before release.", F_FIND, MUT)

    d.text((30, H - 26), "ILLUSTRATIVE   -   a representative run, the numbers shown are not from a real study.",
           font=F_FOOT, fill=DIM)
    return im


def main():
    frames = [draw_frame(s) for s in FRAMES]
    durs = [s["dur"] for s in FRAMES]
    palettized = [im.convert("P", palette=Image.ADAPTIVE, colors=64).convert("RGB") for im in frames]
    imageio.mimsave(OUT, palettized, format="GIF", duration=durs, loop=0)
    size_kb = os.path.getsize(OUT) / 1024
    print(f"[gen_runboard_gif] wrote {os.path.relpath(OUT, ROOT)}  "
          f"({len(frames)} frames, {size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
