#!/usr/bin/env python3
"""cite_export -- reformat and export citations to BibTeX and RIS.

Takes citations you already have -- either an existing BibTeX file
(--bib) or a findings/citation CSV (--findings) -- and re-emits them as
well-formed BibTeX, RIS, or both, in a deterministic order. It is a
formatter, not a fetcher.

Inputs (exactly one of):
  --bib FILE       Parse existing BibTeX entries with a light regex:
                   entry type, cite key, and each field = {value} pair.
  --findings FILE  A findings/citation CSV. The only column that must be
                   present is 'title'; 'authors', 'year', 'doi', 'venue',
                   and 'url' are used when present and ignored when
                   absent. Column names are matched case-insensitively
                   and a few aliases are accepted ('author' for authors,
                   'journal' for venue, 'link' for url, 'date' for year).
                   For CSV input a cite key is synthesized as
                   firstauthorYYYY (or titleslugYYYY / recordN) so output
                   is stable and unique.

Output:
  --format bibtex  (default) | ris | both
  --out FILE       write to a file (default: print to stdout)
  When --format both is written to a file, two files are produced:
  <out>.bib and <out>.ris; when printed to stdout the two blocks are
  concatenated with a separator.

Ordering is deterministic: records are sorted by cite key
(case-insensitive), with first-author-year folded into the synthesized
key for CSV input, so the same input always yields byte-identical
output.

Honest limits: this tool reformats and exports the metadata it is
given. It does NOT fetch, resolve, complete, or verify citations -- it
never touches the network. Missing fields stay missing; a wrong DOI in,
a wrong DOI out. Fetching and verifying citations is the job of
paper_search.py and the citations skill (librarian). Character handling
normalizes whitespace and escapes the characters that would otherwise
break each format (braces and backslashes for BibTeX); it does not
transliterate accents or convert Unicode to LaTeX macros.

Exit codes:
  0  -- export written (records with missing optional fields included)
  1  -- invalid input (missing/unreadable file, no records), or --strict
        with at least one record missing a title (only then)
  2  -- argparse usage errors (argparse default)

Usage:
  python3 tools/cite_export.py --bib refs.bib
  python3 tools/cite_export.py --bib refs.bib --format ris --out refs.ris
  python3 tools/cite_export.py --findings findings_ledger.csv --format both --out export
  python3 tools/cite_export.py --findings cites.csv --strict
Importable:
  from tools.cite_export import parse_bib, load_findings, to_bibtex, to_ris
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import sys

# UTF-8 stdout guard (reconfigures stdout/stderr to UTF-8 on Windows).
import cambium_io  # noqa: F401

TOOL = "cite_export"

# Entry header: @type{key,  -- captured up to the first comma.
_BIB_ENTRY_RE = re.compile(r"(\w+)\s*\{\s*([^,\s}]+)\s*,")
# field = {value} or field = "value"; value has no nested braces (light parse).
_BIB_FIELD_RE = re.compile(r'(\w+)\s*=\s*[{"]([^{}"]*)[}"]')
# Ignore these pseudo-entries when parsing BibTeX.
_BIB_SKIP = {"comment", "preamble", "string"}

# CSV column aliases -> canonical field name. Matched case-insensitively.
_CSV_ALIASES = {
    "title": "title",
    "authors": "authors", "author": "authors",
    "year": "year", "date": "year",
    "doi": "doi",
    "venue": "venue", "journal": "venue", "publisher": "venue",
    "url": "url", "link": "url",
    "key": "key", "citekey": "key", "id": "key",
    "type": "type", "entrytype": "type",
}

# Canonical BibTeX entry type when the source did not provide one.
_DEFAULT_TYPE = "article"

# RIS type by BibTeX entry type (best-effort; JOUR is the safe default).
_RIS_TYPE = {
    "article": "JOUR", "inproceedings": "CPAPER", "conference": "CPAPER",
    "book": "BOOK", "inbook": "CHAP", "incollection": "CHAP",
    "phdthesis": "THES", "mastersthesis": "THES", "techreport": "RPRT",
    "misc": "GEN", "unpublished": "UNPB", "proceedings": "CONF",
}


def _fail(msg: str) -> None:
    print(f"[{TOOL}] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _clean(value: str) -> str:
    """Collapse internal whitespace/newlines and strip; keep it simple."""
    return re.sub(r"\s+", " ", (value or "").replace("\n", " ")).strip()


def _norm_doi(value: str) -> str:
    """Strip a doi.org/ or doi: prefix so the stored DOI is bare."""
    v = _clean(value)
    v = re.sub(r"(?i)^https?://(dx\.)?doi\.org/", "", v)
    v = re.sub(r"(?i)^doi:\s*", "", v)
    return v


def _first_author_surname(authors: str) -> str:
    """Best-effort surname of the first author for key synthesis.

    Accepts 'Last, First; Last2, First2' or 'First Last and First2 Last2'
    or a comma/semicolon list. Falls back to the first alphabetic token.
    """
    a = _clean(authors)
    if not a:
        return ""
    # First author = text before the first ' and ' or ';'.
    first = re.split(r"\s+and\s+|;", a, maxsplit=1)[0].strip()
    if "," in first:
        surname = first.split(",", 1)[0].strip()  # 'Last, First' form
    else:
        parts = first.split()
        surname = parts[-1] if parts else ""       # 'First Last' form
    letters = re.sub(r"[^A-Za-z]", "", surname)
    return letters.lower()


def _slug(text: str, n: int = 12) -> str:
    return re.sub(r"[^a-z0-9]", "", _clean(text).lower())[:n]


def _year_digits(value: str) -> str:
    m = re.search(r"\d{4}", value or "")
    return m.group(0) if m else ""


# ---------------------------------------------------------------------------
# BibTeX input
# ---------------------------------------------------------------------------

def parse_bib(path: str) -> list:
    """Light regex BibTeX parser.

    Returns a list of records: {'key', 'type', <field>: <value>, ...} in
    file order. Only single-level {..} / ".." field values are captured;
    nested braces are out of scope for this light parser.
    """
    if not os.path.isfile(path):
        raise ValueError("bib file not found: %s" % path)
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    records = []
    for chunk in re.split(r"(?m)^\s*@", text)[1:]:
        header = _BIB_ENTRY_RE.match(chunk)
        if not header:
            continue
        etype = header.group(1).lower()
        if etype in _BIB_SKIP:
            continue
        rec = {"type": etype, "key": header.group(2).strip()}
        for k, v in _BIB_FIELD_RE.findall(chunk):
            rec[k.lower()] = _clean(v)
        # Normalize the DOI field if present so output is consistent.
        if rec.get("doi"):
            rec["doi"] = _norm_doi(rec["doi"])
        records.append(rec)
    return records


# ---------------------------------------------------------------------------
# CSV (findings/citation) input
# ---------------------------------------------------------------------------

def load_findings(path: str) -> list:
    """Read a findings/citation CSV into citation records.

    Tolerant of missing columns: only 'title' is expected, and even that
    may be blank on a row (flagged later under --strict). Column names
    are matched case-insensitively via _CSV_ALIASES. A stable cite key is
    synthesized when the CSV does not carry one.
    """
    if not os.path.isfile(path):
        raise ValueError("findings file not found: %s" % path)
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        raw_rows = list(reader)
        header = reader.fieldnames or []
    # Map actual headers -> canonical names once.
    colmap = {}
    for col in header:
        canon = _CSV_ALIASES.get((col or "").strip().lower())
        if canon and canon not in colmap.values():
            colmap[col] = canon

    records = []
    seen_keys = {}
    for i, row in enumerate(raw_rows, 1):
        rec = {}
        for col, canon in colmap.items():
            val = _clean(row.get(col) or "")
            if canon == "doi":
                val = _norm_doi(val)
            elif canon == "year":
                val = _year_digits(val) or val
            if val:
                rec[canon] = val
        rec.setdefault("type", _DEFAULT_TYPE)
        # Synthesize a stable, unique key when absent.
        if not rec.get("key"):
            surname = _first_author_surname(rec.get("authors", ""))
            year = _year_digits(rec.get("year", ""))
            if surname:
                base = surname + (year or "")
            elif rec.get("title"):
                base = _slug(rec["title"]) + (year or "")
            else:
                base = "record%d" % i
            key = base or ("record%d" % i)
        else:
            key = re.sub(r"\s+", "", rec["key"])
        # De-duplicate keys deterministically with a letter suffix.
        if key in seen_keys:
            seen_keys[key] += 1
            key = "%s%s" % (key, chr(ord("a") + seen_keys[key] - 1))
        else:
            seen_keys[key] = 0
        rec["key"] = key
        records.append(rec)
    return records


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

def _sort_records(records: list) -> list:
    """Deterministic order: by cite key (case-insensitive), key as tiebreak."""
    return sorted(records, key=lambda r: ((r.get("key") or "").lower(),
                                          r.get("key") or ""))


# ---------------------------------------------------------------------------
# BibTeX output
# ---------------------------------------------------------------------------

# Field order for BibTeX output: known fields first (stable), extras after.
_BIB_FIELD_ORDER = ["title", "author", "authors", "year", "journal", "venue",
                    "booktitle", "publisher", "volume", "number", "pages",
                    "doi", "url", "abstract"]


def _bib_escape(value: str) -> str:
    """Escape characters that break a BibTeX {value}.

    Backslashes first, then braces. This keeps the field balanced; it does
    not convert accented characters to LaTeX macros (see the docstring).
    """
    v = _clean(value).replace("\\", "\\\\")
    return v.replace("{", "\\{").replace("}", "\\}")


def _bib_fields(rec: dict) -> list:
    """Yield (name, value) field pairs for one record, normalized.

    'authors' is emitted as the BibTeX 'author' field; 'venue' maps to
    'journal' when no explicit journal is present.
    """
    fields = {}
    for k, v in rec.items():
        if k in ("key", "type") or not str(v).strip():
            continue
        name = k
        if k == "authors":
            name = "author"
        elif k == "venue":
            name = "journal"
        # Do not clobber an explicit field with an alias.
        fields.setdefault(name, str(v))
    ordered = [f for f in _BIB_FIELD_ORDER if f in fields]
    ordered += sorted(k for k in fields if k not in _BIB_FIELD_ORDER)
    return [(name, fields[name]) for name in ordered]


def to_bibtex(records: list) -> str:
    """Render records as well-formed, deterministically ordered BibTeX."""
    blocks = []
    for rec in _sort_records(records):
        etype = (rec.get("type") or _DEFAULT_TYPE).lower()
        key = rec.get("key") or "record"
        lines = ["@%s{%s," % (etype, key)]
        pairs = _bib_fields(rec)
        for i, (name, value) in enumerate(pairs):
            comma = "," if i < len(pairs) - 1 else ""
            lines.append("  %s = {%s}%s" % (name, _bib_escape(value), comma))
        lines.append("}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


# ---------------------------------------------------------------------------
# RIS output
# ---------------------------------------------------------------------------

def _ris_authors(value: str) -> list:
    """Split an author string into individual RIS AU values."""
    a = _clean(value)
    if not a:
        return []
    parts = re.split(r"\s+and\s+|;", a)
    return [p.strip() for p in parts if p.strip()]


def _ris_escape(value: str) -> str:
    """RIS is line-oriented; collapse newlines so a value stays on one line."""
    return _clean(value)


def to_ris(records: list) -> str:
    """Render records as RIS (TY/AU/TI/PY/DO/JO/UR/ER), deterministic order."""
    out = []
    for rec in _sort_records(records):
        etype = (rec.get("type") or _DEFAULT_TYPE).lower()
        out.append("TY  - %s" % _RIS_TYPE.get(etype, "JOUR"))
        authors = rec.get("authors") or rec.get("author") or ""
        for au in _ris_authors(authors):
            out.append("AU  - %s" % _ris_escape(au))
        if rec.get("title"):
            out.append("TI  - %s" % _ris_escape(rec["title"]))
        year = _year_digits(rec.get("year", "")) or _clean(rec.get("year", ""))
        if year:
            out.append("PY  - %s" % year)
        venue = rec.get("venue") or rec.get("journal") or ""
        if _clean(venue):
            out.append("JO  - %s" % _ris_escape(venue))
        if rec.get("doi"):
            out.append("DO  - %s" % _ris_escape(rec["doi"]))
        if rec.get("url"):
            out.append("UR  - %s" % _ris_escape(rec["url"]))
        out.append("ER  - ")
        out.append("")  # blank line between records
    return "\n".join(out).rstrip("\n") + ("\n" if out else "")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _missing_titles(records: list) -> list:
    """Return the cite keys of records that have no title."""
    return [r.get("key") or "(no key)" for r in records
            if not _clean(r.get("title", ""))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Reformat and export citations to BibTeX and/or RIS. A "
            "formatter, not a fetcher: it never touches the network and "
            "does not verify or complete citations."
        )
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--bib", default=None,
                     help="existing BibTeX file to parse and re-emit")
    src.add_argument("--findings", default=None,
                     help="findings/citation CSV (needs at least a 'title' column)")
    ap.add_argument("--format", choices=("bibtex", "ris", "both"),
                    default="bibtex", help="output format (default: bibtex)")
    ap.add_argument("--out", default=None,
                    help="output path (default: print to stdout). With "
                         "--format both, writes <out>.bib and <out>.ris.")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any record is missing a title (only then)")
    args = ap.parse_args(argv)

    try:
        if args.bib:
            records = parse_bib(args.bib)
            source_desc = args.bib
        else:
            records = load_findings(args.findings)
            source_desc = args.findings
    except ValueError as exc:
        _fail(str(exc))
        return 1  # unreachable; _fail exits. Keeps type checkers happy.

    if not records:
        _fail("no citation records found in %s" % source_desc)

    missing = _missing_titles(records)
    if missing and args.strict:
        _fail("--strict: %d record(s) missing a title: %s"
              % (len(missing), ", ".join(missing[:8])))

    bib_text = to_bibtex(records) if args.format in ("bibtex", "both") else ""
    ris_text = to_ris(records) if args.format in ("ris", "both") else ""

    if args.out:
        out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
        os.makedirs(out_dir, exist_ok=True)
        written = []
        if args.format == "both":
            base = args.out
            for ext in (".bib", ".ris"):
                if base.endswith(ext):
                    base = base[: -len(ext)]
            bib_path, ris_path = base + ".bib", base + ".ris"
            with open(bib_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(bib_text)
            with open(ris_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(ris_text)
            written = [bib_path, ris_path]
        else:
            text = bib_text if args.format == "bibtex" else ris_text
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            written = [args.out]
        print("[%s] wrote %d record(s) to %s"
              % (TOOL, len(records), ", ".join(written)))
    else:
        if args.format == "both":
            sys.stdout.write(bib_text)
            sys.stdout.write("\n%% ---- RIS ----\n")
            sys.stdout.write(ris_text)
        else:
            sys.stdout.write(bib_text if args.format == "bibtex" else ris_text)

    if missing:
        print("[%s] note: %d record(s) have no title (kept; use --strict to fail)"
              % (TOOL, len(missing)), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
