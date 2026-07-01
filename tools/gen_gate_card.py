#!/usr/bin/env python3
"""gen_gate_card - never present a thin gate.

Renders the FULL gate one-pager (the eight sections in templates/GATE_SUMMARY.md) as a single
self-contained HTML fragment, suitable for mcp__visualize__show_widget. Every gate that reaches a
human must go through this card, or through the equivalent inline board card in
tools/gen_inline_board.py / templates/INLINE_GATE_CARD.html - never a bare "approve?" one-liner.

The eight sections, in fixed order (never reorder, never drop one - see templates/GATE_SUMMARY.md):
  1. Decision needed
  2. Where we are
  3. Options
  4. Risks and open items
  5. Evidence and confidence
  6. Recommendation
  7. Your decision
  8. Director contribution

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
        "director_contribution": "...",
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
    ("director_contribution", "8. Director contribution"),
]

_DEFAULT_YOUR_DECISION = (
    "Reply with one of: APPROVE (proceed with the recommendation), "
    "REVISE (say what to change - it will be re-presented), or REJECT / HOLD (stop here)."
)

_DEFAULT_DIRECTOR_CONTRIBUTION = (
    "This is the half only you can do. Approval is not a signature, it is your thinking, on the "
    "record. Give your hypothesis, your reasoning, your choice and why, and answer the "
    "phase-specific check the Orchestrator poses. A bare APPROVE does not advance the run."
)


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


def _gate_buttons(gate_id):
    gid = esc(gate_id)
    return (
        f'<div class="gc-buttons">'
        f'<button class="gbtn approve" onclick="sendPrompt(\'APPROVE {gid}\')">Approve</button>'
        f'<button class="gbtn revise" onclick="sendPrompt(\'REVISE {gid}: \')">Revise</button>'
        f'<button class="gbtn reject" onclick="sendPrompt(\'REJECT {gid}\')">Reject</button>'
        f'</div>'
        f'<div class="gc-hint">If a button does nothing, type APPROVE, REVISE, or REJECT.</div>'
    )


_STYLE = """
<style>
 .gate-card{font-family:Inter,system-ui,Segoe UI,sans-serif;max-width:640px;margin:0 auto;
   background:#07231A;color:#F4F7F2;border:1px solid #1F4D3B;border-radius:16px;padding:22px 24px}
 .gate-card .gc-head{display:flex;align-items:center;gap:8px;font-size:17px;font-weight:700;color:#16C079}
 .gate-card .gc-q{margin-top:8px;font-size:16px;font-weight:600;color:#F4F7F2;line-height:1.5}
 .gate-card .gc-sub{margin-top:4px;font-size:12.5px;color:#B8C7BE}
 .gate-card .gc-section{margin-top:16px;background:#0E3326;border:1px solid #1F4D3B;border-radius:12px;
   padding:12px 14px}
 .gate-card .gc-section:nth-child(even){background:#15402F}
 .gate-card .gc-label{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
   color:#E0B24A}
 .gate-card .gc-body{margin-top:6px;font-size:13.5px;line-height:1.6;color:#F4F7F2}
 .gate-card .gc-body p{margin:0 0 8px}
 .gate-card .gc-body p:last-child{margin-bottom:0}
 .gate-card .gc-body table{width:100%;border-collapse:collapse;font-size:12.5px}
 .gate-card .gc-body th,.gate-card .gc-body td{border:1px solid #1F4D3B;padding:6px 8px;text-align:left}
 .gate-card .gc-buttons{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap}
 .gate-card .gbtn{cursor:pointer;padding:10px 20px;border-radius:10px;font-weight:800;
   font-size:13px;border:none;font-family:inherit}
 .gate-card .gbtn.approve{background:#16C079;color:#07231A}
 .gate-card .gbtn.revise{background:#E0B24A;color:#07231A}
 .gate-card .gbtn.reject{background:#FF6B5E;color:#07231A}
 .gate-card .gbtn:hover{filter:brightness(1.08)}
 .gate-card .gc-hint{margin-top:9px;font-size:11.5px;color:#B8C7BE}
</style>
""".strip()


def build_gate_card(gate_id, question, sections):
    """Pure function: gate id + one-line question + section dict -> full HTML fragment.

    sections keys (all optional, missing ones render as "not provided yet"):
      decision_needed, where_we_are, options, risks, evidence, recommendation,
      your_decision, director_contribution
    Values may be plain text (escaped) or pre-built HTML (e.g. an options <table>) - the
    heuristic in _is_html() decides which.

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
            else:
                content = "Not provided yet."
        body_parts.append(_section_html(label, content))

    return (
        f'{_STYLE}\n'
        f'<div class="gate-card">'
        f'<div class="gc-head">Gate {esc(gate_id)}</div>'
        f'<div class="gc-q">{esc(question)}</div>'
        f'<div class="gc-sub">Nothing finalizes without you. This is the full one-pager, not a summary.</div>'
        f'{"".join(body_parts)}'
        f'{_gate_buttons(gate_id)}'
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
            "risks": "P0 blockers: none. P1: indirect cost rate not yet reconfirmed with sponsored programs. "
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
