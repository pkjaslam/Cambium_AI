"""Patch script: append one new lesson to each of three thin modules."""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
COURSES = ROOT / "academy" / "courses.json"

with open(COURSES, encoding="utf-8") as f:
    d = json.load(f)

# ── New lessons keyed by module title ────────────────────────────────────────

NEW_LESSONS = {

  "Reproducibility in Practice": {
    "id": "provenance",
    "title": "Seeds, hashes, and run records",
    "subtitle": "Lock every stochastic choice so anyone can rerun and confirm.",
    "blocks": [
      {
        "type": "concept",
        "title": "Three levers that kill silent irreproducibility",
        "html": (
          "<p>Most irreproducible results trace back to three unfixed choices: "
          "<b>random seeds</b> (different runs sample differently), "
          "<b>dependency versions</b> (a library update changes output silently), and "
          "<b>no run record</b> (nobody wrote down what actually executed). "
          "Cambium's Research-Engineer agent locks all three automatically: "
          "it pins the environment in a <code>requirements.txt</code> or <code>environment.yml</code>, "
          "injects a global seed at the top of every script, and writes a "
          "<code>run_record.json</code> that captures the git commit, timestamp, and "
          "SHA-256 hash of every output file. The hash is the receipt: rerun the "
          "code, compare hashes, and you know whether the result is identical.</p>"
        ),
        "why": (
          "A locked seed makes a stochastic pipeline deterministic. "
          "A hash turns 'I think it reproduced' into a verifiable yes or no."
        )
      },
      {
        "type": "predict",
        "q": (
          "You pin the random seed and freeze the environment, then rerun your "
          "analysis. The SHA-256 hash of the output CSV differs from the original. "
          "What is the most likely cause?"
        ),
        "choices": [
          "The seed is working correctly",
          "A data preprocessing step reads files in non-deterministic order",
          "The paper is now published so results change",
          "SHA-256 hashes are expected to differ on rerun"
        ],
        "answer": 1,
        "explain": (
          "Pinning the seed controls sampling, but if an upstream step "
          "reads directory listings or network responses in arbitrary order, "
          "the data entering the analysis can still vary. "
          "The fix is to sort inputs explicitly before processing."
        )
      },
      {
        "type": "flashcards",
        "cards": [
          {
            "front": "Why set a global random seed?",
            "back": (
              "So every stochastic step (sampling, train/test split, model init) "
              "produces the same sequence of numbers on every run."
            )
          },
          {
            "front": "What does a run record capture?",
            "back": (
              "The git commit hash, timestamp, environment snapshot, "
              "and SHA-256 hashes of all output files."
            )
          },
          {
            "front": "How do you confirm a result reproduced exactly?",
            "back": (
              "Rerun the code and compare the SHA-256 hash of the output "
              "against the hash stored in the original run record."
            )
          },
          {
            "front": "What is provenance in Cambium?",
            "back": (
              "The chain of logged steps from raw inputs to final outputs, "
              "including who ran what, when, with which code and data versions."
            )
          }
        ]
      },
      {
        "type": "worked",
        "title": "Add a run record to an existing script",
        "steps": [
          "Add 'import random, hashlib, json, datetime' at the top.",
          "Set 'SEED = 42' and pass it to every random call and to numpy/sklearn.",
          "After writing each output file, compute its SHA-256: "
          "hashlib.sha256(open(path,'rb').read()).hexdigest().",
          "Bundle seed, git commit (from subprocess), timestamp, and hashes "
          "into a dict and write it as run_record.json.",
          "In a fresh virtual environment, rerun the script and confirm "
          "the new run_record.json hashes match the original."
        ],
        "yourturn": {
          "prompt": (
            "A collaborator says your code reproduces, but the output CSV has "
            "a different number of rows on their machine. "
            "What is the first thing you check in the run record?"
          ),
          "hint": "Row count changes without a seed issue usually means the input data changed.",
          "solution": (
            "<p>Check the hash of the input CSV logged in the run record. "
            "If it differs, the collaborator has a different version of the raw data. "
            "Reproducibility of code does not help if the starting data is not identical. "
            "Distribute data with its own hash and document the source.</p>"
          )
        }
      }
    ]
  },

  "Designing Custom Agents": {
    "id": "council",
    "title": "Fitting an agent into a council",
    "subtitle": "One job, one seat, one output contract.",
    "blocks": [
      {
        "type": "concept",
        "title": "Why one job per agent is not a limitation",
        "html": (
          "<p>A Cambium agent that tries to do several things is harder to test, "
          "harder to trust, and harder to swap out. The design rule is: "
          "<b>one job, one seat in a council</b>. "
          "The agent's YAML frontmatter declares its name and a single-sentence description "
          "that a reviewer can evaluate. The output contract specifies the severity "
          "(info, warn, block) and the evidence tier each finding must carry. "
          "When the orchestrator assembles a council, it reads those contracts and "
          "knows exactly what each agent will contribute and what it will not touch.</p>"
          "<p>An agent that raises a <b>block</b>-severity finding halts the run "
          "and routes to a human gate. An agent that raises <b>info</b> adds a note "
          "without stopping anything. Choosing the right severity is part of the design.</p>"
        ),
        "why": (
          "A narrow job means a short, testable system prompt. "
          "A clear output contract means the orchestrator can trust the agent "
          "without reading its internals."
        )
      },
      {
        "type": "predict",
        "q": (
          "You are designing an agent that checks whether a dataset has any "
          "direct PII (names, emails). "
          "It finds a name column. What severity should it raise?"
        ),
        "choices": [
          "info, because the user probably knows",
          "warn, to note it without stopping anything",
          "block, because proceeding with PII present requires human approval",
          "No severity, just log to console"
        ],
        "answer": 2,
        "explain": (
          "Unscreened PII is a hard stop in responsible research. "
          "Block forces a human gate before any further processing. "
          "Warn would let the run continue, which is the wrong default for identifiable data."
        )
      },
      {
        "type": "flashcards",
        "cards": [
          {
            "front": "Where does a custom agent live in Cambium?",
            "back": "As a markdown file in .claude/agents/, with YAML frontmatter declaring name, description, model, and tools."
          },
          {
            "front": "What is an output contract?",
            "back": (
              "A declaration of the severity levels (info/warn/block) and "
              "evidence tiers an agent's findings must carry."
            )
          },
          {
            "front": "Why should a custom agent have exactly one job?",
            "back": (
              "Single-responsibility makes the agent testable with a small "
              "set of cases, and replaceable without changing the rest of the council."
            )
          },
          {
            "front": "What happens when an agent raises a 'block' finding?",
            "back": "The run halts and routes to a human gate for approval before anything continues."
          }
        ]
      },
      {
        "type": "explain",
        "prompt": (
          "You have written an agent that checks for PII and an agent that "
          "checks for data leakage. A colleague suggests merging them into one "
          "agent to save files. Explain why you would keep them separate."
        ),
        "model": (
          "<p>PII checking and leakage checking are two different jobs with "
          "different triggers and different severities. "
          "Merging them makes the system prompt longer and the tests harder to write. "
          "More importantly, if one check needs updating (say, a new leakage rule), "
          "you do not want to risk breaking the PII logic at the same time. "
          "Separate files, separate contracts, separate tests. "
          "The orchestrator composes them into the right council at runtime.</p>"
        )
      }
    ]
  },

  "Teaching Research with Cambium": {
    "id": "learning_gate",
    "title": "The Learning Gate and the learning packet",
    "subtitle": "Turning active research runs into structured student reflection.",
    "blocks": [
      {
        "type": "concept",
        "title": "What the Learning Gate actually does",
        "html": (
          "<p>At the end of every substantial Cambium run the teaching assistant "
          "produces a <b>learning packet</b>: a plain-language summary of what "
          "happened and why, a real architecture diagram of the run, the key decisions "
          "and their tradeoffs, and an open invitation for the student to ask follow-up "
          "questions. This is the Learning Gate.</p>"
          "<p>The gate is not a quiz bolted on at the end. It is built into the run: "
          "the teaching assistant uses the actual artifacts (gate records, evidence tiers, "
          "agent outputs) as teaching material. "
          "The student then gets an interactive Learning Lab with predict-then-reveal "
          "questions, spaced-repetition flashcards, and a 'your turn' change to make. "
          "The Director (instructor or student) must contribute at least one response "
          "before the session closes.</p>"
        ),
        "why": (
          "Reading about research integrity is much weaker than reviewing a real "
          "gate decision you just made. "
          "The learning packet ties the lesson to the student's own work."
        )
      },
      {
        "type": "predict",
        "q": (
          "A student completes a Cambium run and the teaching assistant generates "
          "a learning packet. "
          "What should the student do BEFORE the session closes to satisfy the Learning Gate?"
        ),
        "choices": [
          "Download the final report only",
          "Submit the run to the instructor without reading the packet",
          "Engage with the packet by answering at least one predict-then-reveal question or writing an explain-it-back response",
          "Re-run the entire analysis from scratch"
        ],
        "answer": 2,
        "explain": (
          "The Learning Gate requires active participation, not passive receipt. "
          "The Director must contribute a response so the learning is confirmed, "
          "not just delivered."
        )
      },
      {
        "type": "flashcards",
        "cards": [
          {
            "front": "What is a learning packet?",
            "back": (
              "A plain-language brief produced after a run: what happened, why, "
              "the architecture diagram, key decisions, and an invitation for follow-ups."
            )
          },
          {
            "front": "What is the Learning Gate?",
            "back": (
              "A structured pause after a run where the student engages with the "
              "learning packet before the session is considered complete."
            )
          },
          {
            "front": "How does predict-then-reveal work in a Learning Lab?",
            "back": (
              "The student commits to an answer before seeing the correct one. "
              "This active retrieval strengthens memory compared to just reading the answer."
            )
          },
          {
            "front": "Why must the Director contribute a response at the Learning Gate?",
            "back": (
              "To confirm that learning happened, not just that output was produced. "
              "Passive receipt of a packet is not the same as understanding it."
            )
          }
        ]
      },
      {
        "type": "worked",
        "title": "Design a Learning Gate assignment",
        "steps": [
          "Pick a learning objective: for example, 'student can identify an overclaim in a draft result.'",
          "Set up a Cambium run where the verification agent flags a likely overclaim.",
          "At the gate, require the student to write a 150-word justification for their approve/revise/reject choice.",
          "After the gate, the teaching assistant generates a learning packet using the gate record as evidence.",
          "The student answers the predict-then-reveal block in the lab before submitting.",
          "Grade on the quality of the gate justification and the explain-it-back response, not the final output."
        ],
        "yourturn": {
          "prompt": (
            "Design a Learning Gate moment for a class learning about data leakage. "
            "What does the student see at the gate, and what must they write before continuing?"
          ),
          "hint": (
            "Think about what the verification agent would flag, "
            "and what the student needs to articulate to show they understand it."
          ),
          "solution": (
            "<p>The verification agent flags a suspiciously high AUC (0.97) and notes "
            "that a feature called 'discharge_code' may encode the outcome. "
            "At the gate the student sees the flagged feature, the AUC, and the agent's note. "
            "Before they can continue, they must write: "
            "(1) whether this is likely leakage and why, "
            "(2) what they would remove or change, and "
            "(3) what they expect the AUC to be after the fix. "
            "That three-part response forces the student to reason, not just click approve.</p>"
          )
        }
      }
    ]
  }

}

# ── Patch ────────────────────────────────────────────────────────────────────

patched = []
for mod in d["modules"]:
    title = mod["title"]
    if title in NEW_LESSONS:
        new_lesson = NEW_LESSONS[title]
        # Guard: only append if the lesson id is not already present
        existing_ids = {les["id"] for les in mod["lessons"]}
        if new_lesson["id"] not in existing_ids:
            mod["lessons"].append(new_lesson)
            patched.append(title)

print("Patched modules:", patched)

# ── Validate with json.loads round-trip ──────────────────────────────────────
serialised = json.dumps(d, ensure_ascii=False, indent=1)
d2 = json.loads(serialised)          # verifies it is valid JSON

with open(COURSES, "w", encoding="utf-8") as f:
    f.write(serialised)

print("Written:", COURSES)
print("Lesson counts:")
for mod in d2["modules"]:
    print(f"  {mod['title']}: {len(mod['lessons'])} lesson(s)")
