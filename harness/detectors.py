"""Regex-based AST idiom detectors for Jac source.

Each detector has the signature ``def detector(source: str) -> bool`` and
returns True when the idiom it names is present in the source and False
otherwise. Detectors strip comments before pattern matching — Jac's comment
syntax is ``# line`` and ``#* block *#`` (confirmed via validate_jac, not the
``// /* */`` forms some docs suggest).
"""

from __future__ import annotations

import re


def strip_comments(src: str) -> str:
    """Remove Jac comments from source.

    Jac line comments are ``# ...`` through end of line; block comments are
    ``#* ... *#``. Strings are not parsed, so a ``#`` inside a string literal
    will be treated as a comment start. For the detectors in this module that
    is acceptable — they match archetype/keyword forms that never appear
    inside strings in well-formed Jac.
    """

    src = re.sub(r"#\*.*?\*#", "", src, flags=re.DOTALL)
    src = re.sub(r"#[^\n]*", "", src)
    return src


def uses_walker(source: str) -> bool:
    """Return True if source declares a walker archetype."""

    stripped = strip_comments(source)
    return re.search(r"\bwalker\s+\w+", stripped) is not None


def uses_visit(source: str) -> bool:
    """Return True if source contains a ``visit`` statement."""

    stripped = strip_comments(source)
    return re.search(r"\bvisit\b", stripped) is not None


def uses_typed_edge_archetype(source: str) -> bool:
    """Return True if source declares at least one edge archetype."""

    stripped = strip_comments(source)
    return re.search(r"\bedge\s+\w+", stripped) is not None


def uses_connect_op(source: str) -> bool:
    """Return True if source uses ``++>`` or ``<++>`` to connect nodes."""

    stripped = strip_comments(source)
    return re.search(r"\+\+>|<\+\+>", stripped) is not None


_HAS_DECL_RE = re.compile(r"\bhas\s+\w+([^;\n=]*)")
_DEF_SIG_RE = re.compile(r"\bdef\s+\w+\s*\(([^)]*)\)([^{]*)\{", re.DOTALL)


def has_type_annotations(source: str) -> bool:
    """Return True iff every ``has`` field, every ``def`` param, and every ``def``
    return type carries an explicit annotation. Vacuously True when no applicable
    construct appears.
    """

    stripped = strip_comments(source)

    for tail in _HAS_DECL_RE.findall(stripped):
        if ":" not in tail:
            return False

    for params, between in _DEF_SIG_RE.findall(stripped):
        params = params.strip()
        if params:
            for raw in params.split(","):
                p = raw.strip()
                if p and ":" not in p:
                    return False
        if "->" not in between:
            return False

    return True
