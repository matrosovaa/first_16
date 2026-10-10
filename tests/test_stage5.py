"""Тесты команды chmod, этап 5, вариант 16."""

import copy
import unittest
from io import StringIO

from src.shell import Shell, ShellError, run_script
from src.vfs import VirtualFileSystem

TREE = {
    "a.txt": "a",
    "docs": {"guide.md": "guide", "deep": {"leaf.txt": "leaf"}},
}


def make_shell():
    """Создает оболочку с VFS в памяти."""
    return Shell("test", VirtualFileSystem(copy.deepcopy(TREE), "test"))


def modes(shell, path):
    """Возвращает права узла в виде восьмеричного числа."""
    return shell.vfs.mode(shell.vfs.resolve(shell.cwd, path))


class OctalModeTests(unittest.TestCase):
    """Проверки восьмеричных режимов."""

    def setUp(self):
        self.shell = make_shell()

    def test_default_modes(self):
        self.assertEqual(modes(self.shell, "a.txt"), 0o644)
        self.assertEqual(modes(self.shell, "docs"), 0o755)

    def test_three_digit_mode(self):
        self.shell.run_line("chmod 600 a.txt")
        self.assertEqual(modes(self.shell, "a.txt"), 0o600)

    def test_four_digit_mode(self):
        self.shell.run_line("chmod 0750 docs")
        self.assertEqual(modes(self.shell, "docs"), 0o750)

    def test_short_mode(self):
        self.shell.run_line("chmod 7 a.txt")
        self.assertEqual(modes(self.shell, "a.txt"), 0o007)

    def test_ls_shows_new_mode(self):
        self.shell.run_line("chmod 640 a.txt")
        self.assertIn("-rw-r-----", self.shell.run_line("ls -l"))


class SymbolicModeTests(unittest.TestCase):
    """Проверки символьных режимов."""

    def setUp(self):
        self.shell = make_shell()

    def check(self, mode, expected):
        """Применяет режим к a.txt и сверяет права."""
        self.shell.run_line(f"chmod {mode} a.txt")
        self.assertEqual(modes(self.shell, "a.txt"), expected, mode)

    def test_add(self):
        self.check("u+x", 0o744)

    def test_remove(self):
        self.check("go-r", 0o600)

    def test_assign(self):
        self.check("a=r", 0o444)

    def test_assign_clears_other_bits(self):
        self.check("u=", 0o044)

    def test_several_clauses(self):
        self.check("u=rwx,g=rx,o=", 0o750)

    def test_without_who_means_all(self):
        self.check("+x", 0o755)

    def test_leading_minus_is_a_mode_not_an_option(self):
        self.check("-w", 0o444)

    def test_clauses_are_applied_in_order(self):
        self.check("a+x,o-x", 0o754)

    def test_repeated_letters(self):
        self.check("uu+rrw", 0o644)


class RecursiveAndPathTests(unittest.TestCase):
    """Проверки -R, нескольких путей и ошибок."""

    def setUp(self):
        self.shell = make_shell()

    def test_without_recursion_only_target_changes(self):
        self.shell.run_line("chmod 700 docs")
        self.assertEqual(modes(self.shell, "docs"), 0o700)
        self.assertEqual(modes(self.shell, "docs/guide.md"), 0o644)

    def test_recursive_changes_subtree(self):
        self.shell.run_line("chmod -R 700 docs")
        for path in ("docs", "docs/guide.md", "docs/deep/leaf.txt"):
            self.assertEqual(modes(self.shell, path), 0o700, path)
        self.assertEqual(modes(self.shell, "a.txt"), 0o644)

    def test_recursive_symbolic_keeps_type_specific_bits(self):
        self.shell.run_line("chmod -R go-r docs")
        self.assertEqual(modes(self.shell, "docs"), 0o711)
        self.assertEqual(modes(self.shell, "docs/guide.md"), 0o600)

    def test_option_after_mode(self):
        self.shell.run_line("chmod 700 -R docs")
        self.assertEqual(modes(self.shell, "docs/deep"), 0o700)

    def test_several_paths(self):
        self.shell.run_line("chmod 600 a.txt docs/guide.md")
        self.assertEqual(modes(self.shell, "a.txt"), 0o600)
        self.assertEqual(modes(self.shell, "docs/guide.md"), 0o600)

    def test_relative_to_current_directory(self):
        self.shell.run_line("cd docs")
        self.shell.run_line("chmod 600 guide.md")
        self.assertEqual(modes(self.shell, "/docs/guide.md"), 0o600)

    def test_missing_path_does_not_stop_others(self):
        with self.assertRaisesRegex(ShellError, "'nothing'"):
            self.shell.run_line("chmod 600 nothing a.txt")
        self.assertEqual(modes(self.shell, "a.txt"), 0o600)

    def test_invalid_modes(self):
        for mode in ("999", "1777", "u+z", "rwx", "u+x,", "x+u", "12345"):
            with self.assertRaisesRegex(ShellError, "invalid mode", msg=mode):
                self.shell.run_line(f"chmod {mode} a.txt")
        self.assertEqual(modes(self.shell, "a.txt"), 0o644)

    def test_missing_operands(self):
        with self.assertRaisesRegex(ShellError, "missing operand$"):
            self.shell.run_line("chmod")
        with self.assertRaisesRegex(ShellError, "after '644'"):
            self.shell.run_line("chmod 644")
        with self.assertRaisesRegex(ShellError, "after '644'"):
            self.shell.run_line("chmod -R 644")


class InMemoryTests(unittest.TestCase):
    """Проверка, что данные VFS не изменяются."""

    def test_vfs_data_is_not_modified(self):
        shell = make_shell()
        shell.run_line("chmod -R 000 /")
        self.assertEqual(shell.vfs.data, TREE)

    def test_source_file_is_not_modified(self):
        path = "vfs/project.json"
        with open(path, encoding="utf-8") as file:
            before = file.read()
        vfs = VirtualFileSystem.from_json(path)
        Shell(vfs.name, vfs).run_line("chmod -R 777 /")
        with open(path, encoding="utf-8") as file:
            self.assertEqual(file.read(), before)

    def test_modes_do_not_leak_to_new_vfs(self):
        first = make_shell()
        first.run_line("chmod 600 a.txt")
        self.assertEqual(modes(make_shell(), "a.txt"), 0o644)


class StageFiveScriptTests(unittest.TestCase):
    """Проверка стартового скрипта этапа 5."""

    def test_script_shows_changes_and_errors(self):
        output = StringIO()
        errors = StringIO()
        vfs = VirtualFileSystem.from_json("vfs/project.json")
        shell = Shell(vfs.name, vfs)
        run_script(shell, "scripts/demo_stage5.txt", output, errors)
        self.assertIn("project:/$ chmod 600 docs/guide.md", output.getvalue())
        self.assertIn("-rw-------", output.getvalue())
        self.assertIn("chmod: invalid mode: '999'", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
