"""gen_gate_card: build_gate_card always renders the working buttons, the gate id, no em dashes,
a top decision bar, a themeable (CSS-variable) card, a plain-words glossary, and it suppresses
empty informational sections so the card stays as short as its real content."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_gate_card as G


def test_returns_string():
    h = G.build_gate_card("G-7", "Ship it?", {})
    assert isinstance(h, str) and len(h) > 0


def test_contains_all_three_sendprompt_buttons():
    h = G.build_gate_card("G-7", "Ship it?", {})
    assert "sendPrompt('APPROVE G-7')" in h
    assert "sendPrompt('REVISE G-7: ')" in h
    assert "sendPrompt('REJECT G-7')" in h


def test_contains_gate_id():
    h = G.build_gate_card("G-42", "Approve the plan?", {})
    assert "G-42" in h


def test_no_em_dashes():
    h = G.build_gate_card("G-7", "Ship it?", {
        "decision_needed": "Plain text with no dash of the wrong kind.",
        "options": "<table><tr><td>A</td></tr></table>",
    })
    assert "—" not in h


def test_no_emoji():
    # House rule: no emoji anywhere in the emitted card.
    h = G._demo()
    for ch in h:
        assert ord(ch) < 0x1F000, "emoji-range character leaked into the card: %r" % ch


def test_fallback_line_present():
    h = G.build_gate_card("G-7", "Ship it?", {})
    assert "If a button does nothing, type APPROVE, REVISE, or REJECT." in h


def test_decision_bar_is_near_the_top():
    # Audit #5: the APPROVE/REVISE/REJECT choice must be visible without scrolling. The sticky
    # decision bar (with all three buttons) must appear BEFORE the first content section and before
    # the bottom button block, so it is the first actionable thing on the card.
    h = G._demo()
    bar = h.index('class="gc-bar"')
    first_section = h.index('class="gc-section"')
    bottom_buttons = h.index('class="gc-buttons"')
    assert bar < first_section, "decision bar must come before the first section"
    assert bar < bottom_buttons, "decision bar must come before the bottom button block"
    # The bar itself carries all three real buttons.
    bar_region = h[bar:first_section]
    assert "sendPrompt('APPROVE G-demo')" in bar_region
    assert "sendPrompt('REVISE G-demo: ')" in bar_region
    assert "sendPrompt('REJECT G-demo')" in bar_region
    # And it is sticky so it stays put if the host scrolls the card.
    assert "position:sticky" in h


def test_empty_informational_sections_are_suppressed():
    # Audit #5: no "Not provided yet." fillers. With no content, sections 1-6 must not render.
    h = G.build_gate_card("G-7", "Ship it?", {})
    assert "Not provided yet." not in h
    for label in ("1. Decision needed", "2. Where we are", "3. Options",
                  "4. Risks and open items", "5. Evidence and confidence", "6. Recommendation"):
        assert label not in h, "empty informational section should be suppressed: %s" % label


def test_decision_and_contribution_sections_always_render():
    # Sections 7 and 8 carry the decision and the recorded contribution: always present, even empty.
    h = G.build_gate_card("G-7", "Ship it?", {})
    assert "7. Your decision" in h
    assert "8. Your contribution" in h


def test_provided_sections_render_in_order():
    # A supplied informational section shows up; suppression only drops the empty ones.
    h = G.build_gate_card("G-9", "Go?", {
        "decision_needed": "Decide now.",
        "recommendation": "Do option A.",
    })
    assert "1. Decision needed" in h and "Decide now." in h
    assert "6. Recommendation" in h and "Do option A." in h
    assert "2. Where we are" not in h  # this one was empty -> suppressed
    assert h.index("1. Decision needed") < h.index("6. Recommendation")


def test_uses_css_variables_and_no_bare_hardcoded_slab():
    # Theme defect: the card must adapt to the host theme via CSS variables, not hard-code the dark
    # slab. Every color is a var() with a fallback; the old bare "background:#07231A" (no var) is gone.
    h = G._demo()
    assert "var(--surface-1" in h
    assert "var(--text-primary" in h
    assert "var(--text-accent" in h
    assert "var(--border" in h
    # No BARE hard-coded slab color (the hex may only appear as a var() fallback).
    for bare in ("background:#07231A", "color:#07231A", "background:#0E3326",
                 "color:#16C079", "background:#16C079"):
        assert bare not in h, "bare hard-coded color must be a var() fallback instead: %s" % bare


def test_glossary_present_with_plain_terms():
    # Audit #10: a compact, collapsible plain-words glossary for the jargon on the card.
    h = G._demo()
    assert "What these terms mean" in h
    assert "<details" in h  # collapsible
    for term in ("P0 / P1 / P2", "Code-verified", "Proved", "Asserted",
                 "Mint the token", "NOFO", "F&amp;A"):
        assert term in h, "glossary missing plain-language term: %s" % term


def test_all_section_labels_present_when_all_supplied():
    # When every section has content, all eight labels appear, in the fixed order.
    filled = {key: ("x" if key != "options" else "<table><tr><td>A</td></tr></table>")
              for key, _ in G.SECTION_ORDER}
    h = G.build_gate_card("G-7", "Ship it?", filled)
    last = -1
    for _, label in G.SECTION_ORDER:
        assert label in h
        pos = h.index(label)
        assert pos > last, "sections must render in fixed order"
        last = pos


def test_plain_text_section_is_escaped():
    h = G.build_gate_card("G-7", "Ship it?", {"decision_needed": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in h
    assert "&lt;script&gt;" in h


def test_question_is_escaped_in_the_decision_bar():
    # User-supplied question text is escaped even though it now appears in the top bar.
    h = G.build_gate_card("G-7", "<script>alert('x')</script>", {})
    assert "<script>alert('x')</script>" not in h
    assert "&lt;script&gt;" in h


def test_html_section_passes_through():
    h = G.build_gate_card("G-7", "Ship it?", {"options": "<table><tr><td>A</td></tr></table>"})
    assert "<table><tr><td>A</td></tr></table>" in h


def test_demo_runs():
    h = G._demo()
    assert "G-demo" in h and "sendPrompt('APPROVE G-demo')" in h
