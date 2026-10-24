"""Declared-tool boundaries with the current canonical namespace aliases."""
import unittest
from serve.frontend import OutputParser

DECLARED = [{"name": "write", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}]
GOOD = "<tool_call>\n<function=write>\n<parameter=path>\nhello\n</parameter>\n</function>\n</tool_call>"
BAD = "<tool_call>\n<function=delete_everything>\n<parameter=path>\n/\n</parameter>\n</function>\n</tool_call>"

def events(text, tools, stream, step):
    p = OutputParser(thinking=False, tools=tools, stream_tools=stream)
    result = []
    for i in range(0, len(text), step):
        result.extend(p.feed(text[i:i+step]))
    result.extend(p.finish())
    return result

class DeclaredToolBoundary(unittest.TestCase):
    def test_undeclared_never_executable(self):
        for stream in (False, True):
            for step in (1, 7, 4096):
                with self.subTest(stream=stream, step=step):
                    found = events(BAD, DECLARED, stream, step)
                    self.assertFalse(any(e.kind.startswith("tool_") for e in found), found)
    def test_no_tools_no_executable_call(self):
        self.assertFalse(any(e.kind.startswith("tool_") for e in events(BAD, [], True, 1)))
    def test_truncated_undeclared_suppressed(self):
        for stream in (False, True):
            found = events(BAD[:-24], DECLARED, stream, 1)
            self.assertFalse(any(e.kind.startswith("tool_") for e in found), found)
    def test_declared_namespace_alias(self):
        declared = [{"name": "mcp__websearch.web_search", "parameters": {"type": "object",
                     "properties": {"query": {"type": "string"}}}}]
        output = "<tool_call>\n<function=mcp__websearch__web_search>\n<parameter=query>\nstrata\n</parameter>\n</function>\n</tool_call>"
        for stream in (False, True):
            found = events(output, declared, stream, 1)
            self.assertTrue(any(e.kind == "tool_call" and
                                e.call.name == "mcp__websearch.web_search" for e in found), found)
            self.assertFalse(any(e.kind == "tool_start" and
                                 e.call.name != "mcp__websearch.web_search" for e in found), found)
    def test_mixed_declared_and_undeclared_calls(self):
        for stream in (False, True):
            for step in (1, 7, 4096):
                with self.subTest(stream=stream, step=step):
                    for payload in (GOOD + BAD, BAD + GOOD):
                        found = events(payload, DECLARED, stream, step)
                        calls = [e.call.name for e in found if e.kind == "tool_call"]
                        self.assertEqual(calls, ["write"], found)
                        self.assertFalse(any(e.kind == "tool_start" and
                                             e.call.name != "write" for e in found), found)

    def test_recovery_json_rejects_undeclared(self):
        payload = '<tool_call>{"name": "delete_everything", "arguments": {"path": "/"}}</tool_call>'
        for stream in (False, True):
            parser = OutputParser(thinking=False, tools=DECLARED, stream_tools=stream, recover=True)
            found = []
            for i in range(0, len(payload), 3):
                found.extend(parser.feed(payload[i:i+3]))
            found.extend(parser.finish())
            self.assertFalse(any(e.kind.startswith("tool_") for e in found), found)

    def test_cutoff_unknown_call_never_started(self):
        for stream in (False, True):
            parser = OutputParser(thinking=False, tools=DECLARED, stream_tools=stream)
            found = parser.feed(BAD[:-10]) + parser.finish("length")
            self.assertFalse(any(e.kind.startswith("tool_") for e in found), found)

    def test_declared_preserved(self):
        for stream in (False, True):
            found = events(GOOD, DECLARED, stream, 1)
            self.assertTrue(any(e.kind == "tool_call" and e.call.name == "write" for e in found), found)

if __name__ == "__main__":
    unittest.main()
