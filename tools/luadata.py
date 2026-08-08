"""Parse the engine's generated `data/generated/*.lua` tables into Python.

The generated files are a tiny, regular subset of Lua: one `return { ... }`
table literal built from string/number/boolean scalars, `key = value` records
and positional array items. That is small enough to parse directly and keeps
the authoring tools free of a Lua dependency (there is no standalone lua on
this machine).
"""

from __future__ import annotations

import re

_TOKEN = re.compile(
    r"""
      (?P<ws>\s+|--[^\n]*)
    | (?P<punct>[{}\[\],=])
    | (?P<str>"(?:[^"\\]|\\.)*")
    | (?P<num>-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)
    | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)

_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "'": "'"}


def _unquote(text: str) -> str:
    body = text[1:-1]
    out, i = [], 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _tokenize(src: str):
    pos, end = 0, len(src)
    while pos < end:
        m = _TOKEN.match(src, pos)
        if not m:
            raise ValueError(f"lex error at offset {pos}: {src[pos:pos + 40]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        yield kind, m.group()
    yield "eof", ""


class _Parser:
    def __init__(self, src: str):
        self.toks = list(_tokenize(src))
        self.i = 0

    def peek(self):
        return self.toks[self.i]

    def next(self):
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def expect(self, value):
        kind, text = self.next()
        if text != value:
            raise ValueError(f"expected {value!r}, got {text!r}")

    def parse(self):
        kind, text = self.peek()
        if kind == "name" and text == "return":
            self.next()
        value = self.value()
        return value

    def value(self):
        kind, text = self.next()
        if text == "{":
            return self.table()
        if kind == "str":
            return _unquote(text)
        if kind == "num":
            return float(text) if ("." in text or "e" in text.lower()) else int(text)
        if text == "true":
            return True
        if text == "false":
            return False
        if text == "nil":
            return None
        raise ValueError(f"unexpected token {text!r}")

    def table(self):
        # Records and arrays share the `{}` syntax; a table with any explicit
        # key becomes a dict, a purely positional one becomes a list.
        items, record = [], {}
        while True:
            kind, text = self.peek()
            if text == "}":
                self.next()
                break
            if text == ",":
                self.next()
                continue
            if text == "[":
                self.next()
                key = self.value()
                self.expect("]")
                self.expect("=")
                record[key] = self.value()
                continue
            # `name =` is a record entry; a bare name/number/string/table is
            # a positional item.
            if kind == "name" and self.toks[self.i + 1][1] == "=":
                self.next()
                self.next()
                record[text] = self.value()
                continue
            items.append(self.value())
        if record and items:
            for n, item in enumerate(items, 1):
                record[n] = item
            return record
        return record if record else items


def loads(src: str):
    return _Parser(src).parse()


def load(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return loads(fh.read())
