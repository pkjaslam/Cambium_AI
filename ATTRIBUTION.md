# Attribution

Cambium is MIT-licensed. It incorporates ideas adapted from the following work.

## addyosmani/agent-skills
- **Project:** agent-skills
- **Author / Copyright:** Copyright (c) Addy Osmani
- **Repository:** https://github.com/addyosmani/agent-skills
- **License:** MIT License
- **What Cambium adopted:** the skill-anatomy structural patterns (how a skill file is organized: a
  trigger-rich description, when-to-use, a numbered core process, an anti-rationalization table, explicit
  exit criteria, and red flags). Cambium re-authored this structure as original text. No verbatim files
  were copied. Any future file-level adaptation from this repository will retain the upstream MIT copyright
  and permission notice with the adapted file.

## TaMPER framework
- **Work:** "TaMPER: A Structured Framework for Using Large Language Models in Public Administration Research"
- **Authors:** Michael Overton, Barrie Robison, Luke Sheneman, Jason Cahoon, Sarah Martonick (University of Idaho)
- **Reference:** arXiv:2504.01037 (2025); see also ai4ra.uidaho.edu
- **What Cambium adopted:** the five-step structure (Task, Model, Prompt, Evaluation, Reporting). Cambium's
  `tools/tamper_record.py` produces the record their framework calls for. TaMPER is their contribution, not
  Cambium's; the tool names and credits them in its output.

## UI/UX design skills (ideas adopted into skills/ui-ux-design)
- **ux-ui-agent-skills** by plugin87 - https://github.com/plugin87/ux-ui-agent-skills - the DTCG design-token
  and design-system-preset approach. Idea adopted, no files copied. Verify license before adapting any file.
- **LibreUIUX-Claude-Code** by HermeticOrmus - https://github.com/HermeticOrmus/LibreUIUX-Claude-Code - the
  shared design-vocabulary and tested-prompt review approach. Idea adopted, no files copied.
- **ui-ux-pro-max-skill** by nextlevelbuilder - https://github.com/nextlevelbuilder/ui-ux-pro-max-skill - the
  searchable design-knowledge-base concept. Referenced for a wider style vocabulary.
- **Design Tokens Community Group (DTCG) format** - https://designtokens.org - the open token JSON standard
  the skill recommends for portable tokens.

## Full-stack engineering skill conventions (ideas adopted into docs/engineering_conventions.md and the skills)
- **jeffallan/claude-skills** by Jeff Allan - https://github.com/jeffallan/claude-skills - MIT - the
  progressive-disclosure authoring pattern (thin frontmatter, body on demand), lifecycle and
  skill-combination conventions. Ideas adopted, no files copied.
- **Senior full-stack engineer suite** (mcpmarket / claudepluginhub listings) - no license found - the
  four-dimension definition-of-done scorecard (security, performance, tests, docs) and the architecture-first
  (ADR before scaffolding) stance. Ideas only; nothing copied because no license was found.
- **nextlevelbuilder/ui-ux-pro-max-skill** by nextlevelbuilder - https://github.com/nextlevelbuilder/ui-ux-pro-max-skill -
  MIT - the brief-first design step and versioned design-knowledge-base concept (also credited above under UI/UX).

## OpenMontage
- **Project:** OpenMontage
- **Author / Copyright:** the OpenMontage maintainers (GitHub: calesthio)
- **Repository:** https://github.com/calesthio/OpenMontage
- **License:** GNU Affero General Public License v3.0 (AGPLv3)
- **What Cambium adopted:** no code, text, or prompts. `skills/render-video` calls a separately-installed
  OpenMontage across a process boundary, as an external subprocess; nothing from OpenMontage is bundled or
  copied into this repository, and the user installs it themselves. That process boundary is what keeps
  Cambium's own MIT license clean despite OpenMontage's AGPLv3.

## Microsoft Presidio
- **Project:** Presidio
- **Author / Copyright:** Copyright (c) Microsoft Corporation
- **Repository:** https://github.com/microsoft/presidio
- **License:** MIT License
- **What Cambium adopted:** no Presidio code is copied. `tools/pii_screen.py` uses Presidio as an optional
  dependency for richer, multi-entity detection when it is installed, and falls back to a pure-stdlib regex
  screen when it is not, so the check always runs with no required dependency.

## Loop Engineering research
- **Work:** research framing on the silent costs of autonomous and agentic loops
- **Author / Copyright:** not specified; no canonical author or publisher on file for this framing
- **Reference:** no canonical URL on file
- **License:** not adopted, ideas only
- **What Cambium adopted:** the framing of four silent costs behind `tools/loop_costs.py`: verification
  debt, comprehension rot, cognitive surrender, and token blowout. The detection logic, the reporting, and
  the budget cap are Cambium's own; no text or code was copied.

## Google Open Knowledge Format
- **Work:** Google's Open Knowledge Format, the idea of a portable, cross-linked knowledge bundle
- **Author / Copyright:** Google; no canonical spec document on file
- **Reference:** no canonical URL on file
- **License:** not adopted, ideas only
- **What Cambium adopted:** the portability idea only. `tools/okf_export.py` exports a run as a bundle of
  markdown files with YAML frontmatter, cross-linked, with a self-contained graph viewer. The implementation
  is Cambium's own and does not claim compliance with any formal OKF spec.

## V-JEPA world-model framing
- **Work:** V-JEPA, Meta AI's self-supervised video world-model research
- **Author / Copyright:** Meta AI (FAIR)
- **Reference:** no canonical URL on file
- **License:** not adopted, ideas only
- **What Cambium adopted:** the world-model framing only, de-branded to a heuristic.
  `tools/run_outcome_prior.py` is a statistical prior over Cambium's own historical run logs, not a learned
  model of any kind, and it refuses to fabricate a risk rate on a small sample. No V-JEPA code, weights, or
  text were used.

*Per the MIT license, copyright protects expression, not ideas, so adopting a structural pattern in our own
words does not trigger a notice requirement. We credit the source anyway as good practice. Copying or
closely adapting an actual file would require carrying the upstream MIT notice with that file.*
