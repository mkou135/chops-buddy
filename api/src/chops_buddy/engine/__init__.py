"""Deterministic practice engine.

Rules for this package (DoD A1):
- imports only from the standard library and pydantic;
- no I/O, no clock, no randomness, no model;
- every public function is a pure mapping from inputs to outputs.

Implementation waits for docs/ENGINE_SPEC.md to be merged (DoD A16).
"""
