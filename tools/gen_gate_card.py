#!/usr/bin/env python3
"""gen_gate_card - never present a thin gate, and never a cold one.

Renders the FULL gate one-pager (the sections in templates/GATE_SUMMARY.md) as a single
self-contained HTML fragment, suitable for mcp__visualize__show_widget. Every gate that reaches a
human must go through this card, or through the equivalent inline board card in
tools/gen_inline_board.py / templates/INLINE_GATE_CARD.html - never a bare "approve?" one-liner.

Design goals (UX pass):
  - The APPROVE / REVISE / REJECT choice is visible without scrolling. A compact decision bar sits
    at the TOP of the card (sticky), before the sections, with the gate id and the one-line decision.
    The same three real sendPrompt buttons also repeat at the bottom for reach.
  - The card is as short as its real content. Empty informational sections are suppressed rather
    than padded with "Not provided yet." filler, so a sparse gate stays small.
  - The card adapts to the host chat theme. Colors come from CSS variables (the same vocabulary
    templates/INLINE_GATE_CARD.html uses) with Cambium-teal fallbacks, so it reads in light and dark.
  - Plain words. A small collapsible glossary explains the jargon (P0/P1/P2, the evidence tiers,
    NOFO, F&A, "mint the token") in one line each, for a first-year grad student.

The section order (never reorder - see templates/GATE_SUMMARY.md). Sections 1-6 are shown only when
content is supplied; sections 7 and 8 always render (they carry the Director's decision and the
contribution the gate records):
  1. Decision needed
  2. Where we are
  3. Options
  4. Risks and open items
  5. Evidence and confidence
  6. Recommendation
  7. Your decision
  8. Your contribution

Usage as a library:
    from gen_gate_card import build_gate_card
    html = build_gate_card("G-3", "Ship the draft budget to the sponsor?", {
        "decision_needed": "...",
        "where_we_are": "...",
        "options": "...",       # any of these may be pre-formatted HTML (a <table>, a <ul>, etc.)
        "risks": "...",
        "evidence": "...",
        "recommendation": "...",
        "your_decision": "...",   # optional - a default is supplied if omitted
        "director_contribution": "...",  # optional - a coaching default is supplied if omitted
    })

Usage from the command line:
    python3 tools/gen_gate_card.py            # prints a demo card to stdout
"""
import html
import sys

SECTION_ORDER = [
    ("decision_needed", "1. Decision needed"),
    ("where_we_are", "2. Where we are"),
    ("options", "3. Options"),
    ("risks", "4. Risks and open items"),
    ("evidence", "5. Evidence and confidence"),
    ("recommendation", "6. Recommendation"),
    ("your_decision", "7. Your decision"),
    ("director_contribution", "8. Your contribution"),
]

# Sections 7 and 8 always render (decision + recorded contribution). Everything else is suppressed
# when empty so the card never pads itself with "Not provided yet." fillers.
ALWAYS_SHOWN = {"your_decision", "director_contribution"}

_DEFAULT_YOUR_DECISION = (
    "Reply with one of: APPROVE (proceed with the recommendation), "
    "REVISE (say what to change - it will be re-presented), or REJECT / HOLD (stop here)."
)

# Coaching voice: this reads as an invitation to think out loud, not a form to fill. It still asks
# for exactly what the Learning Gate records (tools/learning_gate.py) - a hypothesis, the reasoning,
# a chosen option, and the Socratic answer - so governance is unchanged; only the tone is warmer.
_DEFAULT_DIRECTOR_CONTRIBUTION = (
    "Before you sign: what do you expect to happen here, and why? A few sentences, in your own "
    "words, is plenty. Tell us what you think this means or expect next, what makes you believe "
    "it, which option you are picking and why, and answer the one question the Orchestrator asks "
    "back. This goes on the record as your call - it is what makes the gate a decision, not a "
    "rubber stamp. A bare APPROVE will not advance the run."
)

# Plain-language glossary. One sentence per term, for a first-year grad student. Only the terms that
# actually turn up on gate cards are here; keep it short and human.
_GLOSSARY = [
    ("P0 / P1 / P2", "How bad a risk is: P0 is a blocker that stops the run, P1 weakens the work, P2 is minor."),
    ("Proved", "Evidence tier: established by a proof or an exact argument, not just a run."),
    ("Code-verified", "Evidence tier: a script actually ran and reproduced the number."),
    ("Asserted", "Evidence tier: stated by an agent but not yet proved or reproduced - trust it least."),
    ("Mint the token", "Record your approval so the run may proceed; nothing advances until it is minted."),
    ("NOFO", "Notice of Funding Opportunity - the funder's call that sets the rules you must meet."),
    ("F&A", "Facilities and Administrative costs (indirect / overhead) - the funder caps how much you may charge."),
]


def esc(s):
    return html.escape(str(s or ""))


import re as _re

# Dangerous constructs are always escaped, even if the content otherwise looks like HTML.
# Sniffing for "<" alone is an injection hole; this blocks scripts, style, embedded frames,
# inline event handlers, and javascript: URLs while still letting a safe table or list through.
_UNSAFE_HTML = _re.compile(
    r"<\s*(script|style|iframe|object|embed|link|meta|svg|base)\b|on\w+\s*=|javascript:",
    _re.IGNORECASE,
)


def _is_html(s):
    """Return True only for content the caller formatted as SAFE HTML (a table, list, or
    emphasis). Plain text, or anything containing a script, style, frame, inline event handler,
    or javascript: URL, returns False so it gets escaped."""
    s = str(s or "")
    if "<" not in s or ">" not in s:
        return False
    if _UNSAFE_HTML.search(s):
        return False
    return True


def _section_html(label, content):
    body = content if _is_html(content) else f"<p>{esc(content)}</p>"
    return (
        f'<div class="gc-section">'
        f'<div class="gc-label">{esc(label)}</div>'
        f'<div class="gc-body">{body}</div>'
        f'</div>'
    )


def _decision_buttons(gate_id):
    """The three real sendPrompt buttons - the only mechanism that posts the decision to chat."""
    gid = esc(gate_id)
    return (
        f'<button class="gbtn approve" onclick="sendPrompt(\'APPROVE {gid}\')">Approve</button>'
        f'<button class="gbtn revise" onclick="sendPrompt(\'REVISE {gid}: \')">Revise</button>'
        f'<button class="gbtn reject" onclick="sendPrompt(\'REJECT {gid}\')">Reject</button>'
    )


def _decision_bar(gate_id, question):
    """Compact sticky bar at the TOP: gate id, one-line decision, and the three buttons - so the
    call is visible without scrolling past the sections below."""
    return (
        f'<div class="gc-bar">'
        f'<div class="gc-bar-text">'
        f'<span class="gc-bar-gate">Gate {esc(gate_id)}</span>'
        f'<span class="gc-bar-q">{esc(question)}</span>'
        f'</div>'
        f'<div class="gc-bar-btns">{_decision_buttons(gate_id)}</div>'
        f'</div>'
    )


def _bottom_actions(gate_id):
    """Repeat the buttons at the foot of a long card, plus the type-it fallback line."""
    return (
        f'<div class="gc-buttons">{_decision_buttons(gate_id)}</div>'
        f'<div class="gc-hint">If a button does nothing, type APPROVE, REVISE, or REJECT.</div>'
    )


def _glossary_html():
    rows = "".join(
        f'<div class="gc-gterm"><span class="gc-gkey">{esc(term)}</span>'
        f'<span class="gc-gdef">{esc(defn)}</span></div>'
        for term, defn in _GLOSSARY
    )
    return (
        f'<details class="gc-gloss">'
        f'<summary>What these terms mean</summary>'
        f'<div class="gc-glist">{rows}</div>'
        f'</details>'
    )


# All colors come from host CSS variables (light/dark aware) with Cambium-teal fallbacks, so the
# card adapts to the chat theme yet keeps its identity if rendered standalone. This mirrors the
# variable vocabulary used in templates/INLINE_GATE_CARD.html.
_STYLE = """
<style>
 .gate-card{font-family:var(--font-sans,Inter,system-ui,Segoe UI,sans-serif);max-width:640px;
   margin:0 auto;background:var(--surface-1,#0E3326);color:var(--text-primary,#F4F7F2);
   border:1px solid var(--border-accent,#1F4D3B);border-radius:16px;overflow:hidden}
 .gate-card .gc-bar{position:sticky;top:0;z-index:5;display:flex;align-items:center;
   justify-content:space-between;gap:12px;flex-wrap:wrap;
   background:var(--surface-2,#07231A);border-bottom:1px solid var(--border-accent,#1F4D3B);
   padding:12px 16px}
 .gate-card .gc-bar-text{min-width:200px;flex:1 1 240px}
 .gate-card .gc-bar-gate{display:block;font-size:12px;font-weight:500;letter-spacing:.04em;
   text-transform:uppercase;color:var(--text-accent,#16C079)}
 .gate-card .gc-bar-q{display:block;margin-top:2px;font-size:14px;font-weight:500;
   color:var(--text-primary,#F4F7F2);line-height:1.45}
 .gate-card .gc-bar-btns{display:flex;gap:8px;flex-wrap:wrap}
 .gate-card .gc-inner{padding:16px 20px 20px}
 .gate-card .gc-sub{font-size:12.5px;color:var(--text-secondary,#B8C7BE);margin-bottom:4px}
 .gate-card .gc-section{margin-top:14px;background:var(--surface-2,#07231A);
   border:1px solid var(--border,#1F4D3B);border-radius:12px;padding:12px 14px}
 .gate-card .gc-section:nth-of-type(even){background:var(--surface-0,#15402F)}
 .gate-card .gc-label{font-size:11px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;
   color:var(--text-warning,#E0B24A)}
 .gate-card .gc-body{margin-top:6px;font-size:13.5px;line-height:1.6;color:var(--text-primary,#F4F7F2)}
 .gate-card .gc-body p{margin:0 0 8px}
 .gate-card .gc-body p:last-child{margin-bottom:0}
 .gate-card .gc-body table{width:100%;border-collapse:collapse;font-size:12.5px}
 .gate-card .gc-body th,.gate-card .gc-body td{border:1px solid var(--border,#1F4D3B);
   padding:6px 8px;text-align:left}
 .gate-card .gc-buttons{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap}
 .gate-card .gbtn{cursor:pointer;padding:9px 18px;border-radius:10px;font-weight:500;font-size:13px;
   font-family:inherit;border:1px solid transparent}
 .gate-card .gc-bar-btns .gbtn{padding:7px 14px;font-size:12.5px}
 .gate-card .gbtn.approve{background:var(--bg-success,#0E3326);color:var(--text-success,#16C079);
   border-color:var(--border-success,#16C079)}
 .gate-card .gbtn.revise{background:var(--bg-warning,#0E3326);color:var(--text-warning,#E0B24A);
   border-color:var(--border-warning,#E0B24A)}
 .gate-card .gbtn.reject{background:var(--bg-danger,#0E3326);color:var(--text-danger,#FF6B5E);
   border-color:var(--border-danger,#FF6B5E)}
 .gate-card .gbtn:hover{filter:brightness(1.08)}
 .gate-card .gc-hint{margin-top:9px;font-size:11.5px;color:var(--text-secondary,#B8C7BE)}
 .gate-card .gc-gloss{margin-top:16px;font-size:12px;color:var(--text-secondary,#B8C7BE)}
 .gate-card .gc-gloss summary{cursor:pointer;color:var(--text-accent,#16C079);font-weight:500;
   list-style:none}
 .gate-card .gc-gloss summary::-webkit-details-marker{display:none}
 .gate-card .gc-gloss summary::before{content:"\\002B  ";font-weight:500}
 .gate-card .gc-gloss[open] summary::before{content:"\\2212  "}
 .gate-card .gc-glist{margin-top:8px;display:grid;gap:6px}
 .gate-card .gc-gterm{display:block;line-height:1.5}
 .gate-card .gc-gkey{font-weight:500;color:var(--text-primary,#F4F7F2)}
 .gate-card .gc-gdef{color:var(--text-secondary,#B8C7BE)}
 .gate-card .gc-gkey::after{content:" - "}
</style>
""".strip()


def build_gate_card(gate_id, question, sections):
    """Pure function: gate id + one-line question + section dict -> full HTML fragment.

    sections keys (all optional):
      decision_needed, where_we_are, options, risks, evidence, recommendation,
      your_decision, director_contribution
    Informational sections (1-6) are rendered only when content is supplied - an empty one is
    dropped, not padded. Sections 7 (your_decision) and 8 (director_contribution) always render,
    with a coaching default when omitted.
    Values may be plain text (escaped) or pre-built HTML (e.g. an options <table>) - the heuristic
    in _is_html() decides which.

    No hidden state: every call with the same arguments returns the same string.
    """
    sections = sections or {}
    body_parts = []
    for key, label in SECTION_ORDER:
        content = sections.get(key)
        if not content:
            if key == "your_decision":
                content = _DEFAULT_YOUR_DECISION
            elif key == "director_contribution":
                content = _DEFAULT_DIRECTOR_CONTRIBUTION
            elif key in ALWAYS_SHOWN:
                content = ""
            else:
                # Suppress empty informational sections instead of padding with filler.
                continue
        body_parts.append(_section_html(label, content))

    return (
        f'{_STYLE}\n'
        f'<div class="gate-card">'
        f'{_decision_bar(gate_id, question)}'
        f'<div class="gc-inner">'
        f'<div class="gc-sub">Nothing finalizes without you. This is the full one-pager, not a summary.</div>'
        f'{"".join(body_parts)}'
        f'{_bottom_actions(gate_id)}'
        f'{_glossary_html()}'
        f'</div>'
        f'</div>'
    )


def _demo():
    return build_gate_card(
        "G-demo",
        "Approve the draft budget narrative for submission to the sponsor?",
        {
            "decision_needed": "Approve or revise the draft budget narrative before it goes to the sponsor.",
            "where_we_are": "Pre-Award finished the first pass. Verification checked the numbers against the "
                            "solicitation caps. Nothing has been sent externally yet.",
            "options": "<table><tr><th>#</th><th>Option</th><th>Upside</th><th>Downside</th><th>Risk</th></tr>"
                       "<tr><td>A</td><td>Submit as drafted</td><td>Fastest path</td><td>No further review</td><td>P1</td></tr>"
                       "<tr><td>B</td><td>One more internal review pass</td><td>Catches more errors</td><td>Adds 2 days</td><td>P2</td></tr>"
                       "<tr><td>C</td><td>Hold, do not submit</td><td>Zero risk of a bad submission</td><td>Misses the deadline</td><td>P0 if deadline slips</td></tr></table>",
            "risks": "P0 blockers: none. P1: indirect cost rate (F&A) not yet reconfirmed with sponsored programs. "
                     "Open: final headcount for year two.",
            "evidence": "Strongest evidence: budget totals reconcile to the narrative line by line, tier "
                        "Code-verified. Produced by Verification - Evidence and Pre-Award - Budget Analyst. "
                        "Confidence in recommendation: 80%. Reject-probability if we proceed: under 15%.",
            "recommendation": "Option A - submit as drafted. The numbers reconcile and the deadline is close; "
                              "a further review pass is unlikely to change the outcome.",
        },
    )


if __name__ == "__main__":
    sys.stdout.write(_demo())
