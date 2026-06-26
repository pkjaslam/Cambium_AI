#!/usr/bin/env python3
"""Cambium — project scaffolder.

Usage:
    python3 tools/new_project.py "<project name>"

Creates:
    projects/<slug>/   — copy of templates/project/
    projects/REGISTRY.md  — appended row (created if absent)

Prints the created path and next steps.
Handles gracefully: missing projects/ dir, existing folder.

No external dependencies — stdlib only.
"""
import os
import re
import shutil
import sys
import datetime

# ── paths relative to repo root ──────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.dirname(SCRIPT_DIR)
TEMPLATE_DIR = os.path.join(REPO_ROOT, "templates", "project")
PROJECTS_DIR = os.path.join(REPO_ROOT, "projects")
REGISTRY     = os.path.join(PROJECTS_DIR, "REGISTRY.md")

# ── helpers ───────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    """Convert a project name to a lowercase-hyphenated slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)          # drop non-word chars
    slug = re.sub(r"[\s_]+", "-", slug)            # spaces/underscores → hyphen
    slug = re.sub(r"-+", "-", slug).strip("-")     # collapse multiple hyphens
    return slug


def next_id(registry_path: str) -> str:
    """Return the next three-digit project ID by counting data rows in the registry."""
    if not os.path.exists(registry_path):
        return "001"
    count = 0
    with open(registry_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            # data rows: start with | and have a digit as first cell content
            if stripped.startswith("|"):
                cells = [c.strip() for c in stripped.split("|")]
                cells = [c for c in cells if c]   # drop empties from split artefacts
                if cells and cells[0].isdigit():
                    count += 1
    return str(count + 1).zfill(3)


def ensure_registry(registry_path: str) -> None:
    """Create REGISTRY.md with header if it does not exist."""
    if os.path.exists(registry_path):
        return
    header = """\
# Projects Registry
*Status: Intake | Ideation | Proposal | Submitted | Approved | Development | Reporting | Closed.
The Director advances status at each gate.*

| ID | Project | Field | Status | Phase / next gate | Folder |
|---|---|---|---|---|---|
"""
    with open(registry_path, "w", encoding="utf-8") as f:
        f.write(header)
    print(f"[new_project] Created {registry_path}")


def append_registry_row(registry_path: str, pid: str, name: str, folder: str) -> None:
    """Append one row to the registry table."""
    row = f"| {pid} | {name} | | Intake | run `read rfp <file>` | {folder}/ |\n"
    with open(registry_path, "a", encoding="utf-8") as f:
        f.write(row)


def copy_template(src: str, dst: str, project_name: str) -> None:
    """Recursively copy template/project/ → dst, substituting <Project Name> in text files."""
    TEXT_EXTS = {".md", ".txt", ".yml", ".yaml", ".csv", ".json", ".py"}

    for root, dirs, files in os.walk(src):
        # Compute destination sub-path
        rel = os.path.relpath(root, src)
        dest_dir = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(dest_dir, exist_ok=True)

        for fname in files:
            src_file  = os.path.join(root, fname)
            dest_file = os.path.join(dest_dir, fname)
            ext = os.path.splitext(fname)[1].lower()

            if ext in TEXT_EXTS:
                with open(src_file, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                content = content.replace("<Project Name>", project_name)
                with open(dest_file, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                shutil.copy2(src_file, dest_file)

# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Usage: python3 tools/new_project.py \"<project name>\"")
        return 1

    project_name = sys.argv[1].strip()
    slug = slugify(project_name)

    if not slug:
        print("[new_project] ERROR: project name produced an empty slug — use letters/numbers.")
        return 1

    # Ensure projects/ directory exists
    os.makedirs(PROJECTS_DIR, exist_ok=True)

    # Determine ID and folder path
    ensure_registry(REGISTRY)
    pid    = next_id(REGISTRY)
    folder = f"{pid}-{slug}"
    dst    = os.path.join(PROJECTS_DIR, folder)

    # Guard against existing folder
    if os.path.exists(dst):
        print(f"[new_project] Folder already exists: {dst}")
        print("[new_project] No changes made. Rename the existing project or choose a different name.")
        return 1

    # Check template exists
    if not os.path.isdir(TEMPLATE_DIR):
        print(f"[new_project] ERROR: template not found at {TEMPLATE_DIR}")
        return 1

    # Copy and register
    copy_template(TEMPLATE_DIR, dst, project_name)
    append_registry_row(REGISTRY, pid, project_name, folder)

    # Report
    print(f"\n[new_project] Project created: {dst}")
    print(f"[new_project] Registry row added: ID={pid}  name='{project_name}'")
    print()
    print("Next steps:")
    print(f"  1. Place your RFP file in {dst}/")
    print(f"  2. Say  `read rfp <filename>`  to start the RFP-Analyst (produces 01_rfp_brief.md).")
    print(f"  3. Approve or decline at Gate G1 (Director decision).")
    print(f"  4. See GETTING_STARTED.md § A for the full pre-award path.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
