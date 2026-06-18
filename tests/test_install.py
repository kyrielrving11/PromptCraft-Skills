"""Tests for install.py — distribution installer.

Run:  python tests/test_install.py
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

INSTALL_PATH = Path(__file__).resolve().parent.parent / "install.py"

# Import install module via importlib so we can mock Path.home() before import
import importlib.util
import sys


def _import_install():
    spec = importlib.util.spec_from_file_location("install", INSTALL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestAutoDetect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_detect_finds_claude_skills(self):
        """When ~/.claude/skills/ exists, it should be detected first."""
        claude_skills = self.tmp_path / ".claude" / "skills"
        claude_skills.mkdir(parents=True)

        with mock.patch.object(Path, "home", return_value=self.tmp_path):
            install = _import_install()
            result = install._detect_target()
            self.assertIsNotNone(result)
            self.assertEqual(result, claude_skills)

    def test_detect_finds_codex_when_claude_missing(self):
        """When ~/.claude/skills/ doesn't exist but ~/.codex/skills/ does,
        it should detect ~/.codex/skills/."""
        codex_skills = self.tmp_path / ".codex" / "skills"
        codex_skills.mkdir(parents=True)

        with mock.patch.object(Path, "home", return_value=self.tmp_path):
            install = _import_install()
            result = install._detect_target()
            self.assertIsNotNone(result)
            self.assertEqual(result, codex_skills)

    def test_detect_finds_codebuddy_as_fallback(self):
        """When neither claude nor codex exist, codebuddy should work."""
        cb_skills = self.tmp_path / ".codebuddy" / "skills"
        cb_skills.mkdir(parents=True)

        with mock.patch.object(Path, "home", return_value=self.tmp_path):
            install = _import_install()
            result = install._detect_target()
            self.assertIsNotNone(result)
            self.assertEqual(result, cb_skills)

    def test_detect_returns_none_when_none_exist(self):
        """When no known skills directory exists, return None."""
        with mock.patch.object(Path, "home", return_value=self.tmp_path):
            install = _import_install()
            result = install._detect_target()
            self.assertIsNone(result)


class TestVersionTracking(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_and_read_version(self):
        install = _import_install()
        install._write_version(self.tmp_path)
        version = install._read_version(self.tmp_path)
        self.assertEqual(version, install.VERSION)

    def test_read_version_no_file(self):
        install = _import_install()
        version = install._read_version(self.tmp_path / "nonexistent")
        self.assertIsNone(version)

    def test_read_version_corrupted(self):
        install = _import_install()
        version_file = self.tmp_path / install.VERSION_FILE
        version_file.write_text("{bad json", encoding="utf-8")
        version = install._read_version(self.tmp_path)
        self.assertIsNone(version)

    def test_version_file_content(self):
        install = _import_install()
        install._write_version(self.tmp_path)
        version_file = self.tmp_path / install.VERSION_FILE
        data = json.loads(version_file.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], install.VERSION)
        self.assertEqual(data["skills"], install.SKILL_NAMES)


class TestInstallOperations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        # Create a mock source skills directory
        self.src = self.tmp_path / "source" / "skills"
        self.src.mkdir(parents=True)
        for name in ["prompt-craft", "prompt-memory",
                     "prompt-techniques", "prompt-review"]:
            skill_dir = self.src / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name}", encoding="utf-8")
        self.target = self.tmp_path / "target"

    def tearDown(self):
        self.tmp.cleanup()

    def _get_install(self):
        install = _import_install()
        # Patch _skills_source to return our mock source
        install._skills_source = lambda: self.src
        return install

    def test_copy_tree_creates_files(self):
        install = self._get_install()
        install._copy_tree(self.src / "prompt-craft",
                           self.target / "prompt-craft")
        self.assertTrue((self.target / "prompt-craft" / "SKILL.md").exists())

    def test_copy_tree_overwrites_existing(self):
        install = self._get_install()
        dst = self.target / "prompt-craft"
        dst.mkdir(parents=True)
        (dst / "old_file.txt").write_text("old")
        install._copy_tree(self.src / "prompt-craft", dst)
        self.assertTrue((dst / "SKILL.md").exists())
        self.assertFalse((dst / "old_file.txt").exists())

    def test_symlink_or_copy_fallback(self):
        """On Windows, symlink often fails without admin — ensure fallback to copy."""
        install = self._get_install()
        dst = self.target / "prompt-craft-sym"
        install._symlink_tree(self.src / "prompt-craft", dst)
        # Either symlink or copy — the file should be there
        self.assertTrue(dst.exists())
        self.assertTrue((dst / "SKILL.md").exists())

    def test_remove_tree_removes(self):
        install = self._get_install()
        d = self.target / "to-remove"
        d.mkdir(parents=True)
        (d / "file.txt").write_text("data")
        result = install._remove_tree(d, "to-remove")
        self.assertTrue(result)
        self.assertFalse(d.exists())

    def test_remove_tree_not_found(self):
        install = self._get_install()
        result = install._remove_tree(self.target / "nope", "nope")
        self.assertFalse(result)

    def test_install_all_skills(self):
        install = self._get_install()
        with mock.patch.object(Path, "home", return_value=self.tmp_path):
            for name in install.SKILL_NAMES:
                install._copy_tree(self.src / name, self.target / name)
            # All four should be present
            for name in install.SKILL_NAMES:
                self.assertTrue((self.target / name / "SKILL.md").exists())

    def test_version_written_after_install(self):
        install = self._get_install()
        install._write_version(self.target)
        self.assertTrue((self.target / install.VERSION_FILE).exists())
        v = install._read_version(self.target)
        self.assertEqual(v, install.VERSION)


class TestCheckUpdate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_check_update_up_to_date(self):
        install = _import_install()
        install._write_version(self.tmp_path)
        # Should not raise — same version
        version = install._read_version(self.tmp_path)
        self.assertEqual(version, install.VERSION)

    def test_check_update_mismatch(self):
        install = _import_install()
        version_file = self.tmp_path / install.VERSION_FILE
        version_file.write_text(
            json.dumps({"version": "v1.0", "skills": install.SKILL_NAMES}),
            encoding="utf-8",
        )
        version = install._read_version(self.tmp_path)
        self.assertEqual(version, "v1.0")
        self.assertNotEqual(version, install.VERSION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
