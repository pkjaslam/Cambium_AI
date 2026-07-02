#!/usr/bin/env python3
"""gen_inline_board — the IN-CHAT live Cambium run board (a show_widget fragment).

gen_board_pro.py renders the SIDEBAR board (a standalone HTML artifact you can reopen). THIS renders the
same run as an inline, claude-native widget fragment for `mcp__visualize__show_widget`: agent boxes that
read done / working / waiting, a progress rail, each agent's one-line finding, and — when a gate is live —
a clickable APPROVE / REVISE / REJECT card whose buttons actually post the decision to chat (sendPrompt).

It reads the live `agent_outputs/run_state.json` (auto-discovered, same as the sidebar board), so re-running
it at the start of each phase gives the Director a board that updates in place. Output is a bare HTML
fragment (no <html>/<head>/<body>) — exactly what show_widget wants. The agent pipes stdout into the
widget_code field.

  python3 tools/gen_inline_board.py [--state agent_outputs/run_state.json] [--title "<request>"]
"""
import argparse, html, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import cambium_io  # reconfigures stdout/stderr to UTF-8 on Windows; provides data_home()
import gen_board_pro as P  # reuse load() + status_of() so the two boards never disagree

def esc(s): return html.escape(str(s or ""))

STYLE = """<style>
@keyframes cbps{0%,100%{opacity:1}50%{opacity:.25}}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
@media (prefers-reduced-motion: reduce){*{animation:none !important;transition:none !important}}
.cb-gb:focus-visible{outline:2px solid var(--text-accent);outline-offset:2px}
.cb-ag{display:flex;gap:12px;align-items:flex-start;padding:13px 15px;border:0.5px solid var(--border);border-radius:12px;background:var(--surface-2);margin-bottom:9px}
.cb-ag.wait{opacity:.55}
.cb-ic{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--bg-accent);color:var(--text-accent);flex:none}
.cb-tag{font-size:12px;font-weight:500;padding:3px 9px;border-radius:999px;background:var(--bg-accent);color:var(--text-accent)}
.cb-find{font-size:13.5px;color:var(--text-secondary);margin-top:6px;line-height:1.55;border-left:2px solid var(--border-success);padding-left:9px}
.cb-st{font-size:12px;font-weight:500;display:flex;align-items:center;gap:5px;flex:none}
.cb-gate{border:2px solid var(--border-accent);border-radius:12px;background:var(--surface-1);padding:16px;margin:6px 0 10px}
.cb-gb{padding:8px 16px;border-radius:var(--radius);font-size:14px;font-weight:500;border:0.5px solid var(--border-strong);background:var(--surface-2);cursor:pointer}
.cb-gb.ap{border-color:var(--border-success);color:var(--text-success)}
.cb-gb.rv{border-color:var(--border-warning);color:var(--text-warning)}
.cb-gb.rj{border-color:var(--border-danger);color:var(--text-danger)}
.cb-upnext{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:11px 14px;border:0.5px dashed var(--border);border-radius:12px;background:var(--surface-1);margin-top:6px;font-size:12.5px;color:var(--text-secondary)}
.cb-un-lbl{font-weight:600;color:var(--text-accent);text-transform:uppercase;letter-spacing:.5px;font-size:11px;margin-right:4px}
.cb-un-chip{display:inline-flex;align-items:center;gap:6px;color:var(--text-primary);font-weight:500}
.cb-un-chip::before{content:"";width:8px;height:8px;border-radius:50%;border:1.5px solid var(--text-muted)}
</style>"""

def render(state_path, title):
    d, phases, cur, note = P.load(state_path)
    n_ag = sum(len(p.get("agents", [])) for p in phases)
    n_co = len({a[0] for p in phases for a in p.get("agents", [])})
    n_gt = sum(1 for p in phases if p.get("gate"))
    done_ph = sum(1 for i, _ in enumerate(phases) if P.status_of(i, cur) == "done")
    total = len(phases) or 1
    pct = round(100 * done_ph / total)
    req = title or d.get("plan", {}).get("request") or note or "Cambium run"

    pill = ("Run complete" if (cur and cur > total) else
            (f"Phase {cur} of {total}" if cur else "Convening"))

    boxes = []
    upnext = []
    seen_ids = set()   # no duplicate live chip in a single rendered view (audit #7)
    fmap = d.get("findings") or {}
    smap = d.get("agent_status") or {}
    for i, p in enumerate(phases):
        st = P.status_of(i, cur)            # done / now / waiting
        if st == "waiting":
            upnext.append(p)                # collapse not-yet-started phases (audit #4)
            continue
        for a in p.get("agents", []):
            council, role = (a + ["", ""])[:2]
            aid = a[2] if len(a) > 2 else role
            # resolve finding/status by AGENT ID from the top-level maps (the shape
            # run_state.py writes: agents are 3-tuples, finding/status live in the maps);
            # fall back to any value embedded on the tuple (a[3]/a[4]) so the old shape works.
            finding = fmap.get(aid, a[3] if len(a) > 3 else "")
            arec = smap.get(aid, a[4] if len(a) > 4 else "queued")
            if aid in seen_ids:
                continue
            seen_ids.add(aid)
            eff = P._eff_status(st, arec)   # per-agent live status inside the running phase
            if eff == "done":
                stht = '<div class="cb-st" style="color:var(--text-success)"><i class="ti ti-check" aria-hidden="true"></i>done</div>'
                show_find = bool(finding)
            elif eff == "working":
                stht = '<div class="cb-st" style="color:var(--text-warning)"><span style="width:8px;height:8px;border-radius:50%;background:var(--text-warning);animation:cbps 1s infinite"></span>working</div>'
                show_find = bool(finding)
            else:
                stht = '<div class="cb-st" style="color:var(--text-muted)"><i class="ti ti-clock" aria-hidden="true"></i>queued</div>'
                show_find = False
            boxes.append(
                f'<div class="cb-ag" role="listitem">'
                f'<div class="cb-ic"><i class="ti ti-user-cog" aria-hidden="true"></i></div>'
                f'<div style="flex:1;min-width:0">'
                f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
                f'<span class="cb-tag">{esc(council)}</span>'
                f'<span style="font-weight:600;font-size:14.5px">{esc(role)}</span></div>'
                + (f'<div class="cb-find">{esc(finding)}</div>' if show_find else "")
                + f'</div>{stht}</div>')

    # compact "Up next" strip for not-yet-started councils (audit #4): one chip per phase,
    # "<council> (n)", never one card per queued agent.
    upnext_html = ""
    if upnext:
        chips = "  ->  ".join(
            f'<span class="cb-un-chip">{esc(p.get("council",""))} ({len(p.get("agents", []))})</span>'
            for p in upnext)
        upnext_html = (f'<div class="cb-upnext"><span class="cb-un-lbl">Up next</span>{chips}</div>')

    # active gate (the pending one)
    gatecard = ""
    armed = d.get("gate") or {}
    active = next((p["gate"] for i, p in enumerate(phases)
                   if p.get("gate") and P.status_of(i, cur) == "now"), None)
    gid = armed.get("id") or (active or {}).get("id")
    gq = armed.get("decision") or (active or {}).get("decision") or "Approve to proceed?"
    if gid:
        gatecard = (
          f'<div class="cb-gate"><div style="display:flex;align-items:center;gap:8px;font-weight:500;font-size:15px;color:var(--text-accent)">'
          f'<i class="ti ti-shield-check" aria-hidden="true"></i>Gate {esc(gid)} — your decision</div>'
          f'<div style="font-size:13px;color:var(--text-secondary);margin:6px 0 14px;line-height:1.5">{esc(gq)} '
          f'Nothing finalizes without you.</div>'
          f'<div style="display:flex;gap:8px;flex-wrap:wrap" role="group" aria-label="Gate decision">'
          f'<button class="cb-gb ap" onclick="sendPrompt(\'APPROVE {esc(gid)}\')"><i class="ti ti-check" aria-hidden="true"></i> Approve</button>'
          f'<button class="cb-gb rv" onclick="sendPrompt(\'REVISE {esc(gid)}: \')"><i class="ti ti-rotate" aria-hidden="true"></i> Revise</button>'
          f'<button class="cb-gb rj" onclick="sendPrompt(\'REJECT {esc(gid)}\')"><i class="ti ti-x" aria-hidden="true"></i> Reject</button></div></div>')

    done_banner = ""
    if cur and cur > total:
        done_banner = ('<div style="border:0.5px solid var(--border-success);background:var(--bg-success);'
                       'border-radius:12px;padding:14px;margin-top:6px;font-size:13px;color:var(--text-success);'
                       'display:flex;align-items:center;gap:8px"><i class="ti ti-circle-check" aria-hidden="true"></i>'
                       'Run complete — every phase cleared its gate.</div>')

    frag = (
      f'<h2 class="sr-only">Live Cambium run board for {esc(req)}: agent boxes and approval gates.</h2>'
      + STYLE +
      f'<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin:.5rem 0 1rem">'
      f'<div style="display:flex;align-items:center;gap:10px">'
      f'<i class="ti ti-building-bank" style="font-size:24px;color:var(--text-accent)" aria-hidden="true"></i>'
      f'<div><div style="font-weight:500;font-size:16px">Cambium Institute</div>'
      f'<div style="font-size:13px;color:var(--text-secondary)">{esc(req)}</div></div></div>'
      f'<div style="text-align:right"><div style="font-size:12px;font-weight:500;color:var(--text-accent)">{esc(pill)}</div>'
      f'<div style="font-size:12px;color:var(--text-muted)">{n_ag} agents · {n_co} councils · {n_gt} gate(s)</div></div></div>'
      f'<div style="height:6px;background:var(--surface-1);border-radius:999px;overflow:hidden;margin-bottom:1rem">'
      f'<div style="height:100%;width:{pct}%;background:var(--text-accent);transition:width .5s"></div></div>'
      + gatecard + f'<div class="cb-list" role="list" aria-live="polite" aria-label="Agent activity">' + "".join(boxes) + f'</div>' + upnext_html + done_banner)
    return frag

def main(argv=None):
    ap = argparse.ArgumentParser()
    # Default state path uses data_home() so it works even when ROOT is read-only (plugin install).
    # In the dev/repo/test case, data_home() == ROOT, so behavior is unchanged.
    ap.add_argument("--state", default=os.path.join(cambium_io.data_home(), "agent_outputs", "run_state.json"))
    ap.add_argument("--title", default="")
    ap.add_argument("--out", default="", help="optional file to write the fragment to (else stdout)")
    a = ap.parse_args(argv)
    if not os.path.exists(a.state):
        print("[gen_inline_board] no run state at %s — run cambium_start.py first." % a.state); return 1
    frag = render(a.state, a.title)
    if a.out:
        # Resolve relative --out against data_home(), not ROOT.
        out = a.out if os.path.isabs(a.out) else os.path.join(cambium_io.data_home(), a.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(frag)
        try:
            shown = os.path.relpath(out, ROOT)
        except ValueError:
            shown = out
        print("[gen_inline_board] wrote %s (%d chars) — pass to show_widget" % (shown, len(frag)))
    else:
        sys.stdout.write(frag)
    return 0

if __name__ == "__main__":
    sys.exit(main())
