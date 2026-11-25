"""Check that regenerated bundles retain the complete game voice skill contract."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".codebuddy/skills/cs-game-voice-gen"
TREES = ("skills", ".agents/skills", ".claude/skills", ".gemini/skills", "plugins/claude/skills")


class GameVoiceGenAdapterTests(unittest.TestCase):
    def test_all_runtime_resources_and_body_match_source(self):
        for tree in TREES:
            bundle = ROOT / tree / "cs-game-voice-gen"
            for source in SOURCE.rglob("*"):
                if not source.is_file():
                    continue
                relative = source.relative_to(SOURCE)
                with self.subTest(tree=tree, file=str(relative)):
                    target = bundle / relative
                    self.assertTrue(target.is_file(), str(target))
                    if relative.as_posix() == "SKILL.md":
                        body = lambda path: re.sub(r"\A---\n.*?\n---\n", "", path.read_text(encoding="utf-8"),
                                                   count=1, flags=re.DOTALL)
                        self.assertEqual(body(source), body(target))
                    else:
                        self.assertEqual(source.read_bytes(), target.read_bytes())

    def test_local_reference_links_resolve_in_each_bundle(self):
        for bundle in [SOURCE] + [ROOT / tree / "cs-game-voice-gen" for tree in TREES]:
            for document in bundle.rglob("*.md"):
                for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                    if "://" not in link and not link.startswith("#"):
                        with self.subTest(file=str(document), link=link):
                            self.assertTrue((document.parent / link.split("#")[0]).is_file())

    def test_codex_prompt_invokes_the_skill(self):
        command = (ROOT / ".codex/prompts/cs-game-voice-gen.md").read_text(encoding="utf-8")
        self.assertIn("Invoke the cs-game-voice-gen skill and follow its workflow for: $ARGUMENTS", command)


if __name__ == "__main__":
    unittest.main()
