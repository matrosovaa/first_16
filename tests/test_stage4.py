"""Тесты команд ls, cd, date и find, этап 4, вариант 16."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from src.shell import Shell, ShellError, run_script
from src.vfs import VirtualFileSystem

TREE = {
    "README.md": "readme",
    "notes.txt": "root",
    "docs": {"guide.md": "guide", "notes.txt": "docs", "empty": {}},
    "src": {"main.py": "print()", "utils": {"helpers.py": "pass"}},
}
FIXED_TIME = datetime(2026, 10, 10, 14, 30, 5, tzinfo=timezone.utc)


def make_shell():
    """Создает оболочку с фиксированными VFS и временем."""
    vfs = VirtualFileSystem(TREE, "project")
    return Shell("project", vfs, clock=lambda: FIXED_TIME)


class LsTests(unittest.TestCase):
    """Проверки команды ls."""

    def setUp(self):
        self.shell = make_shell()

    def test_root_listing_is_sorted(self):
        self.assertEqual(
            self.shell.run_line("ls"), "README.md\ndocs\nnotes.txt\nsrc"
        )

    def test_listing_by_relative_and_absolute_path(self):
        expected = "empty\nguide.md\nnotes.txt"
        self.assertEqual(self.shell.run_line("ls docs"), expected)
        self.assertEqual(self.shell.run_line("ls /docs"), expected)

    def test_file_is_printed_as_given(self):
        self.assertEqual(self.shell.run_line("ls docs/guide.md"),
                         "docs/guide.md")

    def test_empty_directory_prints_nothing(self):
        self.assertIsNone(self.shell.run_line("ls docs/empty"))

    def test_long_format(self):
        lines = self.shell.run_line("ls -l docs").split("\n")
        self.assertEqual(lines[0], "drwxr-xr-x   4096 empty")
        self.assertEqual(lines[1], "-rw-r--r--      5 guide.md")

    def test_missing_path(self):
        with self.assertRaisesRegex(ShellError, "No such file"):
            self.shell.run_line("ls missing")

    def test_invalid_option(self):
        with self.assertRaisesRegex(ShellError, "invalid option"):
            self.shell.run_line("ls -z")

    def test_too_many_arguments(self):
        with self.assertRaisesRegex(ShellError, "too many"):
            self.shell.run_line("ls docs src")


class CdTests(unittest.TestCase):
    """Проверки команды cd."""

    def setUp(self):
        self.shell = make_shell()

    def test_cd_changes_directory_and_prompt(self):
        self.shell.run_line("cd src/utils")
        self.assertEqual(self.shell.cwd, "/src/utils")
        self.assertEqual(self.shell.prompt(), "project:/src/utils$ ")

    def test_cd_relative_listing(self):
        self.shell.run_line("cd src")
        self.assertEqual(self.shell.run_line("ls"), "main.py\nutils")

    def test_cd_parent_and_root(self):
        self.shell.run_line("cd src/utils")
        self.shell.run_line("cd ../..")
        self.assertEqual(self.shell.cwd, "/")
        self.shell.run_line("cd /docs")
        self.shell.run_line("cd")
        self.assertEqual(self.shell.cwd, "/")

    def test_cd_above_root_stays_in_root(self):
        self.shell.run_line("cd ../../..")
        self.assertEqual(self.shell.cwd, "/")

    def test_cd_errors_keep_directory(self):
        self.shell.run_line("cd docs")
        for line in ("cd missing", "cd guide.md", "cd a b"):
            with self.assertRaises(ShellError):
                self.shell.run_line(line)
        self.assertEqual(self.shell.cwd, "/docs")


class DateTests(unittest.TestCase):
    """Проверки команды date."""

    def setUp(self):
        self.shell = make_shell()

    def test_default_format(self):
        self.assertEqual(
            self.shell.run_line("date"), "Sat Oct 10 14:30:05 UTC 2026"
        )

    def test_custom_format(self):
        self.assertEqual(self.shell.run_line("date +%Y-%m-%d"), "2026-10-10")

    def test_invalid_date(self):
        with self.assertRaisesRegex(ShellError, "invalid date"):
            self.shell.run_line("date tomorrow")

    def test_too_many_arguments(self):
        with self.assertRaisesRegex(ShellError, "too many"):
            self.shell.run_line("date +%Y +%m")


class FindTests(unittest.TestCase):
    """Проверки команды find."""

    def setUp(self):
        self.shell = make_shell()

    def test_find_without_arguments_lists_everything(self):
        lines = self.shell.run_line("find").split("\n")
        self.assertEqual(lines[0], ".")
        self.assertIn("./src/utils/helpers.py", lines)
        self.assertEqual(len(lines), 11)

    def test_find_keeps_path_as_typed(self):
        lines = self.shell.run_line("find docs").split("\n")
        self.assertEqual(lines[0], "docs")
        self.assertEqual(lines[1], "docs/empty")

    def test_find_by_name(self):
        self.assertEqual(
            self.shell.run_line("find / -name notes.txt"),
            "/docs/notes.txt\n/notes.txt",
        )

    def test_find_by_name_pattern_and_type(self):
        self.assertEqual(
            self.shell.run_line("find -type f -name '*.py'"),
            "./src/main.py\n./src/utils/helpers.py",
        )

    def test_find_directories_only(self):
        self.assertEqual(
            self.shell.run_line("find src -type d"), "src\nsrc/utils"
        )

    def test_find_uses_current_directory(self):
        self.shell.run_line("cd src")
        self.assertEqual(
            self.shell.run_line("find -name helpers.py"),
            "./utils/helpers.py",
        )

    def test_find_nothing_prints_nothing(self):
        self.assertIsNone(self.shell.run_line("find -name nothing"))

    def test_find_errors(self):
        for line in (
            "find /missing",
            "find -name",
            "find -size 1",
            "find -type x",
        ):
            with self.assertRaises(ShellError, msg=line):
                self.shell.run_line(line)


class StageFourScriptTests(unittest.TestCase):
    """Проверка стартового скрипта этапа 4."""

    def test_script_runs_with_prompt_and_errors(self):
        output = StringIO()
        errors = StringIO()
        vfs = VirtualFileSystem.from_json("vfs/project.json")
        shell = Shell(vfs.name, vfs)
        run_script(shell, "scripts/demo_stage4.txt", output, errors)
        self.assertIn("project:/$ ls docs", output.getvalue())
        self.assertIn("project:/src/utils$ ls -l", output.getvalue())
        self.assertIn("cd: README.md: Not a directory", errors.getvalue())


class VfsLoadTests(unittest.TestCase):
    """Проверки загрузки VFS этапа 4."""

    def test_invalid_node_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps({"dir": {"n": 1}}), encoding="utf-8")
            with self.assertRaisesRegex(ShellError, "invalid node"):
                VirtualFileSystem.from_json(path)


if __name__ == "__main__":
    unittest.main()
