"""cambium_io — UTF-8 stdout/stderr guard for Windows terminals.

On Windows the default console encoding is cp1252 (or similar narrow codepage), which
cannot represent the Unicode glyphs Cambium tools print (⛔ ✓ ⬢ ⛩ · ─ ▶ ○ …).
Any print() hitting those chars raises UnicodeEncodeError and exits the tool nonzero,
causing ~18 test failures on Windows that do not appear on Linux/CI.

Import this module as early as possible in any tool that prints non-ASCII characters.
It reconfigures stdout and stderr to UTF-8 *in process*, so no env-var (PYTHONIOENCODING)
or terminal setting is required by the caller.  The try/except swallows the AttributeError
raised on streams that do not support reconfigure() (e.g. already-replaced StringIO in tests).
"""
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
