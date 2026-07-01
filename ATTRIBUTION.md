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

*Per the MIT license, copyright protects expression, not ideas, so adopting a structural pattern in our own
words does not trigger a notice requirement. We credit the source anyway as good practice. Copying or
closely adapting an actual file would require carrying the upstream MIT notice with that file.*
