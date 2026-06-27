"""Test speed/cost telemetry helpers (deterministic, no API calls)."""
import os, sys, csv, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import cambium_run as cr
def test_estimate_cost_known_models():
    assert cr.estimate_cost("claude-sonnet-4-6", {"input_tokens":1_000_000,"output_tokens":0}) == 3.0
    assert cr.estimate_cost("claude-opus-4-8", {"input_tokens":0,"output_tokens":1_000_000}) == 75.0
    assert cr.estimate_cost("unknown-model", {"input_tokens":1_000_000,"output_tokens":0}) == 3.0  # fallback
def test_log_cost_writes_header_then_rows():
    d=tempfile.mkdtemp(); p=os.path.join(d,"cost_log.csv")
    cr.log_cost(p, ["r1","produce","deck-builder","claude-sonnet-4-6",100,50,1.2,0.0015])
    cr.log_cost(p, ["r1","produce","figures","claude-haiku-4-5-20251001",80,40,0.5,0.0003])
    rows=list(csv.reader(open(p)))
    assert rows[0]==["run","phase","agent","model","input_tokens","output_tokens","wall_s","est_usd"]
    assert len(rows)==3 and rows[1][2]=="deck-builder"
