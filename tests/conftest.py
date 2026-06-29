"""Test environment defaults.

Some tools (gate_lock.py) sign one-time tokens with a salt taken from CAMBIUM_GATE_SALT.
When that env var is unset, each process invents a fresh random salt, so a token minted in
one subprocess cannot be verified in another and the gate/resume tests fail. CI does not set
the var, so we pin a deterministic salt for the whole test session. Production still uses the
real env var; this only affects tests.
"""
import os
os.environ.setdefault("CAMBIUM_GATE_SALT", "cambium-deterministic-test-salt")
