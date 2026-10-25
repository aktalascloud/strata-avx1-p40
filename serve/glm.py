"""GLM's native call syntax over the existing declared-tool authorization boundary.

The model writes NAME<arg_key>K</arg_key><arg_value>V</arg_value>.
No global function marker is weakened and no undeclared name becomes a tool event.
Format reference: PolyStrata c174f35 (MIT); streaming integration is local.
"""
from __future__ import annotations
import json
import re
from serve.frontend import CALL_START, CALL_END, Event, OutputParser, ToolCall

KEY, KEY_END = "<arg_key>", "</arg_key>"
VALUE, VALUE_END = "<arg_value>", "</arg_value>"
NAME_LIMIT = 600

def name_of(body: str, complete=False):
    stops = [p for p in (body.find(KEY), body.find(CALL_END)) if p >= 0]
    if stops:
        return body[:min(stops)].strip()
    return body.strip() if complete else None

def value_end(text: str, complete=False) -> int:
    at = text.find(VALUE_END)
    while at >= 0:
        tail = text[at + len(VALUE_END):].lstrip()
        if tail.startswith(KEY) or tail.startswith(CALL_END) or (complete and not tail):
            return at
        if not tail or KEY.startswith(tail) or CALL_END.startswith(tail):
            return -2
        at = text.find(VALUE_END, at + len(VALUE_END))
    return -1

def call_end(body: str) -> int:
    """Only a closer after the name or a value closes a call; literal tags stay values."""
    pos = body.find(CALL_END)
    while pos >= 0:
        before = body[:pos].rstrip()
        if before.endswith(VALUE_END) or KEY not in before:
            return pos
        pos = body.find(CALL_END, pos + len(CALL_END))
    return -1

def typed(value, declared):
    if declared == "string":
        return value
    try:
        return json.loads(value)
    except ValueError:
        return value

def parse_call(body: str, schema=None):
    name = name_of(body, complete=True)
    at = body.find(KEY)
    rest = body[at:] if at >= 0 else ""
    properties = ((schema or {}).get("parameters") or {}).get("properties") or {}
    args = {}
    while rest.strip():
        rest = rest.lstrip()
        if not rest.startswith(KEY):raise ValueError("malformed GLM argument")
        end = rest.find(KEY_END, len(KEY))
        if end < 0:raise ValueError("incomplete GLM argument key")
        key = rest[len(KEY):end].strip()
        if not key or len(key) > NAME_LIMIT or any(x in key for x in "<>"):raise ValueError("invalid GLM argument key")
        if key in args:raise ValueError("duplicate GLM argument")
        rest = rest[end + len(KEY_END):].lstrip()
        if not rest.startswith(VALUE):raise ValueError("missing GLM argument value")
        rest = rest[len(VALUE):];end = value_end(rest, complete=True)
        if end < 0:raise ValueError("incomplete GLM argument value")
        args[key] = typed(rest[:end], (properties.get(key) or {}).get("type"))
        rest = rest[end + len(VALUE_END):]
    return ToolCall(name=name, arguments=args)

class GlmOutputParser(OutputParser):
    native_call_format = True

    def _reset_scan(self):
        super()._reset_scan();self._glm_complete = False;self._glm_keys = set()

    def _body_name(self, body):
        return name_of(body, complete=True)

    def _body_end(self, body):
        return call_end(body)

    def _parse_body(self, body, schema):
        return parse_call(body, schema)

    def _quoted_think_end(self, i):
        # The GLM template permits an answer immediately after </think>, including after a quote.
        return False

    def _native_open(self, i, out):
        after = self.buf[i + len(CALL_START):].lstrip()
        name = name_of(after)
        prefix = after[:after.find("<")] if "<" in after else after
        partial = after[after.find("<"):] if "<" in after else ""
        if (name is None and len(after) <= NAME_LIMIT and re.fullmatch(r"\S*\s*", prefix)
                and (not partial or KEY.startswith(partial) or CALL_END.startswith(partial))):
            j = i
            while j > 0 and self.buf[j - 1] == "\n":j -= 1
            if j > 0:out.append(Event("content", self._track(self.buf[:j])));self.buf = self.buf[j:]
            return "wait"
        canonical = self.aliases.get(name, name) if name else None
        if not name or len(name) > NAME_LIMIT or canonical not in self.schemas:
            self.unread += 1
            if name and len(self.unread_names) < 5:self.unread_names.append(name[:80])
            out.append(Event("content", self._track(self.buf[:i + len(CALL_START)])))
            self.buf = self.buf[i + len(CALL_START):]
            return "text"
        if i and self.buf[:i].strip():out.append(Event("content", self._track(self.buf[:i].rstrip("\n"))))
        self.buf = self.buf[i + len(CALL_START):];self.state = "call"
        return "call"

    def _wrapped_call_end(self):
        end = call_end(self.buf);self._glm_complete = end >= 0
        return end

    def _scan(self):
        out = []
        def args(s):
            if s:out.append(Event("tool_args", s, call=self.scall))
        while True:
            rest = self.buf[self.sp:]
            if self.ss == "name":
                raw = name_of(rest, complete=self._glm_complete)
                if raw is None:return out
                name = self.aliases.get(raw, raw)
                if name not in self.schemas:self.ss = "blocked";return out
                self.scall = ToolCall(name=name, arguments={})
                props = ((self.schemas[name].get("parameters") or {}).get("properties") or {})
                self.sdeclared = {k:(v or {}).get("type") for k,v in props.items()}
                out.append(Event("tool_start", call=self.scall));args("{")
                at = rest.find(KEY);self.sp += at if at >= 0 else len(rest);self.ss = "between"
            elif self.ss == "between":
                stripped = rest.lstrip();self.sp += len(rest) - len(stripped)
                if not stripped.startswith(KEY):return out
                end = stripped.find(KEY_END, len(KEY))
                if end < 0:return out
                key = stripped[len(KEY):end].strip()
                if not key or len(key) > NAME_LIMIT or any(x in key for x in "<>") or key in self._glm_keys:
                    raise ValueError("invalid or duplicate GLM argument key")
                tail = stripped[end + len(KEY_END):];padding = len(tail)-len(tail.lstrip());tail = tail.lstrip()
                if not tail.startswith(VALUE):return out
                self._glm_keys.add(key)
                args(("" if self.sfirst else ",") + json.dumps(key) + ":");self.sfirst = False
                self.sp += end + len(KEY_END) + padding + len(VALUE)
                self.ss = "str" if self.sdeclared.get(key) == "string" else "raw"
                if self.ss == "str":args('"')
            elif self.ss in ("str", "raw"):
                end = value_end(rest, complete=self._glm_complete)
                if end >= 0:
                    if self.ss == "str":args(json.dumps(rest[:end])[1:-1] + '"')
                    else:args(json.dumps(typed(rest[:end], None), ensure_ascii=False))
                    self.sp += end + len(VALUE_END);self.ss = "between"
                elif self.ss == "raw":return out
                else:
                    safe = rest.find(VALUE_END) if end == -2 else len(rest) - self._hold(rest, (VALUE_END,))
                    if safe > 0:args(json.dumps(rest[:safe])[1:-1]);self.sp += safe
                    return out
            else:return out

def to_glm_force(force):
    if not force:return force
    marker = "<function=";at = force.find(marker)
    name = force[at + len(marker):] if at >= 0 else ""
    if name.endswith(">\n"):name = name[:-2] + "\n"
    return CALL_START + name
