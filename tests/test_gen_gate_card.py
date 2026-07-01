"""gen_gate_card: build_gate_card always renders the working buttons, the gate id, no em dashes."""
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


def test_fallback_line_present():
    h = G.build_gate_card("G-7", "Ship it?", {})
    assert "If a button does nothing, type APPROVE, REVISE, or REJECT." in h


def test_all_eight_sections_present_even_when_omitted():
    h = G.build_gate_card("G-7", "Ship it?", {})
    for _, label in G.SECTION_ORDER:
        assert label in h


def test_plain_text_section_is_escaped():
    h = G.build_gate_card("G-7", "Ship it?", {"decision_needed": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in h
    assert "&lt;script&gt;" in h


def test_html_section_passes_through():
    h = G.build_gate_card("G-7", "Ship it?", {"options": "<table><tr><td>A</td></tr></table>"})
    assert "<table><tr><td>A</td></tr></table>" in h


def test_demo_runs():
    h = G._demo()
    assert "G-demo" in h and "sendPrompt('APPROVE G-demo')" in h
