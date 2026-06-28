#!/usr/bin/env python3
"""Cambium model router (v3.3 — adds a reasoning tier).

Maps each agent to a concrete model via:
  agent's own tier (opus/sonnet/haiku/inherit, from agent_cards.json)
    -> router tier name (strong/mid/light)
      -> concrete model string of the ACTIVE provider (from config.yml).

NEW: a REASONING layer for the hardest judgment work (verification boards, theory, statistics). Claude's
extended thinking is the same strong model run with a thinking budget, so reasoning is expressed honestly as
"strong model + a test-time thinking budget", not a different vendor. The budget scales with difficulty
(test-time scaling). Whether the budget is honored is up to the runner (Claude Code / the SDK); this router
emits the recommendation. Other providers stay pluggable via config.yml.

Usage:
  python3 tools/model_router.py                 # full agent->model table (marks reasoning agents)
  python3 tools/model_router.py <agent>         # resolve one agent, with its thinking budget
  python3 tools/model_router.py <agent> --budget hard   # test-time scaling: low|normal|hard|max
Importable:  from tools.model_router import route ; route("verify-rigor")
"""
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIER_OF = {"opus": "strong", "inherit": "strong", "sonnet": "mid", "haiku": "light"}

# the hardest judgment work gets extended thinking (the "reasoning tier")
REASONING_AGENTS = {"verify-rigor", "verify-methodology", "verify-evidence", "referee",
                    "lab-theory", "lab-statistics"}
# test-time scaling: thinking-token budget by difficulty (0 = no extended thinking)
THINKING_BUDGET = {"off": 0, "low": 4000, "normal": 8000, "hard": 16000, "max": 32000}

def load_config():
    for name in ("config.yml", "config.example.yml"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            try:
                import yaml
                return yaml.safe_load(open(p, encoding="utf-8")), name
            except Exception:
                break
    return {"model_router": {"active_provider": "anthropic", "providers": {"anthropic": {"enabled": True,
            "tiers": {"strong": "claude-opus-4-8", "mid": "claude-sonnet-4-6",
                      "light": "claude-haiku-4-5-20251001"}}}}}, "(built-in defaults)"

def active_tiers(cfg):
    mr = cfg.get("model_router", {})
    prov = mr.get("active_provider", "anthropic")
    p = mr.get("providers", {}).get(prov, {})
    if not p.get("enabled", False):
        raise SystemExit("[router] active_provider '%s' is not enabled in config." % prov)
    tiers = p.get("tiers", {})
    missing = [t for t in ("strong", "mid", "light") if not tiers.get(t)]
    if missing:
        raise SystemExit("[router] provider '%s' is missing models for tiers: %s" % (prov, missing))
    return prov, tiers

def load_cards():
    p = os.path.join(ROOT, "agent_cards.json")
    if not os.path.exists(p):
        raise SystemExit("[router] agent_cards.json not found - run tools/gen_agent_cards.py first.")
    return {a["name"]: a.get("model", "inherit") for a in json.load(open(p))["agents"]}

def resolve(name, cards, tiers):
    """Unchanged: returns (router_tier, model) using strong/mid/light. Backwards compatible."""
    agent_tier = cards.get(name, "inherit")
    rt = TIER_OF.get(agent_tier, "mid")
    return rt, tiers[rt]

def thinking_budget(name, difficulty="hard"):
    """Test-time thinking budget for an agent. Reasoning agents get extended thinking; others get 0."""
    if name in REASONING_AGENTS:
        return THINKING_BUDGET.get(difficulty, THINKING_BUDGET["hard"])
    return 0

def route(name, difficulty="hard"):
    """Full routing decision for an agent: model + whether to use extended thinking + the budget."""
    cfg, _ = load_config()
    _, tiers = active_tiers(cfg)
    cards = load_cards()
    rt, model = resolve(name, cards, tiers)
    budget = thinking_budget(name, difficulty)
    return {"agent": name, "tier": ("reasoning" if budget else rt), "model": model,
            "extended_thinking": bool(budget), "thinking_budget": budget}

def main():
    args = sys.argv[1:]
    difficulty = args[args.index("--budget") + 1] if "--budget" in args else "hard"
    pos = [a for a in args if not a.startswith("--") and a != difficulty]
    cfg, src = load_config()
    prov, tiers = active_tiers(cfg)
    cards = load_cards()
    if pos:
        r = route(pos[0], difficulty)
        tag = (" + extended thinking (%d tok)" % r["thinking_budget"]) if r["extended_thinking"] else ""
        print("[router] %s -> tier=%s -> %s%s (provider=%s)" % (r["agent"], r["tier"], r["model"], tag, prov))
        return 0
    print("[router] config=%s | provider=%s | %d agents | %d on the reasoning tier" % (
        src, prov, len(cards), sum(1 for n in cards if n in REASONING_AGENTS)))
    for name in sorted(cards):
        rt, model = resolve(name, cards, tiers)
        b = thinking_budget(name, difficulty)
        mark = "  <reasoning %dtok>" % b if b else ""
        print("  %-26s -> %-7s %s%s" % (name, rt, model, mark))
    return 0

if __name__ == "__main__":
    sys.exit(main())
