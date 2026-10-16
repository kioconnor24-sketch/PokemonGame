"""Directed agent messages must remain safe, observable, and non-authoritative."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "coordination"
SPEC = importlib.util.spec_from_file_location("messages", ROOT / "messages.py")
MSG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MSG)
R_SPEC = importlib.util.spec_from_file_location("board", ROOT / "render_board.py")
BOARD = importlib.util.module_from_spec(R_SPEC)
R_SPEC.loader.exec_module(BOARD)

BASE_URL = "https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-"


def note(ident=123, body=None, assoc="OWNER"):
    return {
        "id": ident, "html_url": BASE_URL + str(ident),
        "author_association": assoc, "created_at": "2026-10-15T22:00:00Z",
        "body": body or ("AGENT_MESSAGE TO=claude KIND=ANSWER TASK=SCRIPTED-BATTLE PR=#25\n"
                         "SUMMARY: Codex verified 0x4003 can be a candidate.\n"
                         "NEXT: Wait for exclusive file handoff and test in-process load."),
    }


class MessagesTests(unittest.TestCase):
    def test_exact_directed_message_routes_only_to_claude(self):
        parsed = MSG.parse([note()])
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["task"], "SCRIPTED-BATTLE")
        self.assertEqual(parsed[0]["pr"], 25)
        self.assertIn("0x4003", MSG.markdown(parsed, "claude"))
        self.assertNotIn("0x4003", MSG.markdown(parsed, "codex"))
        self.assertIn("source comment", MSG.markdown(parsed, "claude"))

    def test_untrusted_author_cannot_insert_message(self):
        self.assertEqual(MSG.parse([note(assoc="NONE")]), [])

    def test_invalid_headers_and_untrusted_urls_are_ignored(self):
        variants = [
            note(body="I will now quote:\nAGENT_MESSAGE TO=claude KIND=ANSWER TASK=Q\nSUMMARY: yes\nNEXT: go"),
            note(body="AGENT_MESSAGE TO=claude KIND=APPROVED TASK=Q\nSUMMARY: yes\nNEXT: go"),
            note(body="AGENT_MESSAGE TO=claude KIND=ANSWER TASK=Q\nSUMMARY: yes"),
        ]
        evil = note(999)
        evil["html_url"] = "https://attacker.example/handoff#issuecomment-999"
        self.assertEqual(MSG.parse(variants + [evil]), [])

    def test_ack_is_advisory_not_a_handoff(self):
        ack = note(200, body="AGENT_ACK ID=123 BY=claude")
        entries = MSG.parse([note(), ack])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["acknowledged_by"], ["claude"])
        self.assertIn("ACK REPORTED", MSG.markdown(entries, "claude"))
        self.assertNotIn("ACK REPORTED", MSG.markdown(entries, "codex"))

    def test_wrong_ack_identity_does_not_suppress_target(self):
        ack = note(200, body="AGENT_ACK ID=123 BY=codex")
        parsed = MSG.parse([note(), ack])
        self.assertIn("AWAITING ACK", MSG.markdown(parsed, "claude"))

    def test_broadcast_reaches_all(self):
        n = note(body="AGENT_MESSAGE TO=all KIND=FYI TASK=QUEST\n"
                      "SUMMARY: Q1 awaits actual screenshots.\n"
                      "NEXT: Read #23 before claiming a fix.")
        parsed = MSG.parse([n])
        for agent in ("codex", "claude", "playtest"):
            self.assertIn("Q1", MSG.markdown(parsed, agent))

    def test_renderer_includes_messages_but_no_automatic_approval(self):
        conf = {"tasks": [{"id": "Q", "agent": "codex", "pr": 14, "deps": [],
                           "qa_cases": ["Q1"], "next": "Wait for QA"}]}
        snap = {
            "main_sha": "a"*40, "generated_at": "fixture",
            "pull_requests": [
                {"number": 14, "state": "open", "merged": False,
                 "head_sha": "b"*40, "checks": "success"}
            ], "qa_signoffs": [], "communications": [note()],
        }
        rendered = BOARD.render(conf, snap)
        self.assertIn("Codex inbox", rendered["board"])
        self.assertIn("0x4003", rendered["claude"])
        self.assertIn("OPEN PR / QA PENDING", rendered["board"])
        self.assertIn("No automated agent launch", rendered["board"])

    def test_newest_unacknowledged_messages_first(self):
        first = note(100, body="AGENT_MESSAGE TO=claude KIND=FYI TASK=A\n"
                               "SUMMARY: first\nNEXT: first next")
        last = note(200, body="AGENT_MESSAGE TO=claude KIND=QUESTION TASK=B\n"
                              "SUMMARY: second\nNEXT: answer")
        ack = note(300, body="AGENT_ACK ID=200 BY=claude")
        parsed = MSG.parse([first, last, ack])
        selected = MSG.for_agent(parsed, "claude")
        self.assertEqual([x["id"] for x in selected], [100, 200])


if __name__ == "__main__":
    unittest.main()
