# Changelog

## 1.0.0 - Initial public release
- 34-agent, 9-council research institute (orchestration, pre-award, partnerships, faculty, scouts,
  labs, verification, execution, support, reporting).
- Full project lifecycle (RFP -> proposal -> development -> reports) with 6 human-in-the-loop gates.
- Output contract (severity + claim tiers), findings ledger, leaderboard, synthesis.
- Smart-Tier model profile (+ opus-max / lean).
- Template repo + installable plugin manifest + marketplace.json.
- Interactive dashboard; two fictional demo projects.

## 1.1.0 - Governance & self-audit
- Ran the Institute on itself (Project 003): 4 audit boards; objectives scorecard.
- Added AI_GOVERNANCE.md (research + teaching) and AI_USE_STATEMENT.md template.
- Added governance/GATES.md (recorded human approvals) and governance/validate.py (evidence-tier
  validator + provenance manifest; fails build on open P0). Added SECURITY.md, CODE_OF_CONDUCT.md.
- README/INSTITUTE/OUTPUT_CONTRACT updated to reference governance.

## 1.2.0 - Team roles & delegated human-in-the-loop
- Added ROLES.md: Director/PI, Co-PI/Area Lead, Project Manager(Admin), Researcher/Student, Engineer,
  independent Integrity/Data steward; human->agent mapping; separation of duties; worked team example.
- config.example.yml now defines the team roster + per-gate approver map (delegated approvals).
- GATES.md gains role + named-approver columns. Each PI/Co-PI is the human-in-the-loop for their sector.

## 1.3.0 - World-class release (Institute built by its own team)
- CI: tools/check_agents.py (frontmatter validator) + .github/workflows/validate.yml — the evidence
  contract is now enforced on every push/PR (green on a healthy repo, red on an open P0 or invalid agent).
- Demo: demo/tour.html — a 60-second self-running animated tour; README gets badges + above-the-fold value prop.
- Worked example: examples/full-lifecycle/ — a complete fictional RFP->proposal->development->verify->
  report artifact chain that PASSES validate.py (demonstrates the integration claim end to end).
- Team usability: tools/whoami.py (prints a person's desk + approvable gates) + TEAM_QUICKSTART.md.
- tools/quickstart.sh + quickstart.ps1 one-command setup.

## 1.4.0 - High-end release
- Landing site: index.html (polished one-pager) + .github/workflows/pages.yml (GitHub Pages deploy).
- Visuals: assets/org-chart.svg + assets/lifecycle.svg (render on GitHub); embedded in README "At a glance".
- Positioning: COMPARISON.md (honest, web-verified vs AI Scientist / Co-Scientist / Agent Lab / AutoGen),
  FAQ.md, ROADMAP.md, CITATION.cff (citable software).
- Field-agnostic proof: examples/demo-humanities + examples/demo-public-health (non-STEM).
- tools/new_project.py scaffolder. Test artifacts moved to tools/test_fixtures/; projects/REGISTRY.md reset.

## 2.0.0 - Deeper research capability (v2)
- Roster 34 -> 39 (all doers/referees): lab-statistics, exec-iteration, research-engineer, referee, idea-tournament.
- Adopted (verified) mechanisms: novelty gate (AI Scientist), Elo idea tournament + reflect/evolve
  (AI Co-Scientist), scored self-refinement + tree-search experiment loop (Agent Lab / AI Scientist),
  venue-rubric referee (AI Scientist), cross-project institutional memory (AutoGen).
- New triggers: run tournament, iterate experiment, referee, run verification debate.
- Upgraded record-keeper (institutional memory), scout-prior-art (novelty gate), ideation (feeds tournament).
- See CAMBIUM_V2.md.

## 3.0.0 - Full research lifecycle (v3)
- Roster 39 -> 45: rfp-radar, convener, budget-officer, grants-compliance, feedback-router, research-conduct-officer.
- End-to-end lifecycle (LIFECYCLE_V3.md): RFP radar -> idea inbox -> brainstorm/tournament -> team + pre-award
  (budget, biosketch, DMP, forms) -> award mobilize (assignments, scoped agent access, alerts) -> execute ->
  reports/meetings/scheduling -> feedback router. New gate G0 (Know the PI).
- Responsible-research governance at EVERY gate (RESEARCH_CONDUCT.md): IRB/IACUC, COI, FERPA, data
  sovereignty, dual-use, reproducibility - GO / CONDITIONS / STOP, alongside evidence + AI-use governance.
- Templates: USER_PROFILE, IDEA_INBOX, COLLAB_WORKSPACE, POST_AWARD_PLAN.
- New triggers: watch rfps, rfp in <file>, add idea, convene team, build budget, compliance check,
  assign work, route feedback, conduct check <gate>.
- See CAMBIUM_V3.md.
