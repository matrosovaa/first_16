"""Тесты этапов 1-3 эмулятора, вариант 16."""

import json
import os
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src.shell import (
    Config,
    Shell,
    ShellError,
    ShellExit,
    build_prompt,
    parse_line,
    print_config,
    run_script,
)
from src.vfs import VirtualFileSystem


class ParserTests(unittest.TestCase):
    """Проверки prompt и парсера."""

    # Этап 1: имя VFS должно быть в prompt.
    def test_prompt_contains_vfs_name(self):
        self.assertEqual(build_prompt("myvfs"), "myvfs$ ")

    # Этап 1: парсер разделяет ввод.
    def test_parse_line(self):
        self.assertEqual(
            parse_line("ls -l /tmp"), ("ls", ["-l", "/tmp"])
        )

    # Этап 1: раскрываем переменную окружения.
    def test_environment_expansion(self):
        with patch.dict(os.environ, {"HOME": "/home/student"}):
            self.assertEqual(
                parse_line("ls $HOME"), ("ls", ["/home/student"])
            )


class CommandTests(unittest.TestCase):
    """Проверки команд первого этапа."""

    def setUp(self):
        self.shell = Shell("vfs16")

    # Этап 1: ls пока является заглушкой.
    def test_ls_stub(self):
        self.assertEqual(self.shell.run_line("ls /tmp -l"), "ls: /tmp -l")

    # Этап 1: cd пока является заглушкой.
    def test_cd_stub(self):
        self.assertEqual(self.shell.run_line("cd /home"), "cd: /home")

    # Этап 1: неизвестная команда дает ошибку.
    def test_unknown_command(self):
        with self.assertRaises(ShellError):
            self.shell.run_line("unknown")

    # Этап 1: проверяем число аргументов.
    def test_argument_error(self):
        with self.assertRaises(ShellError):
            self.shell.run_line("cd one two")

    # Этап 1: команда exit завершает оболочку.
    def test_exit(self):
        with self.assertRaises(ShellExit):
            self.shell.run_line("exit")


class ConfigTests(unittest.TestCase):
    """Проверки конфигурации этапа 2."""

    # Этап 2: выводим параметры запуска.
    def test_print_config(self):
        output = StringIO()
        print_config(Config("vfs/test.json", "scripts/test.txt"), output)
        self.assertIn("VFS path: vfs/test.json", output.getvalue())
        self.assertIn("Script path: scripts/test.txt", output.getvalue())

    # Этап 2: игнорируем комментарии скрипта.
    def test_script_comments_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "start.txt"
            script.write_text(
                "# comment\nls file.txt\nexit\n", encoding="utf-8"
            )
            output = StringIO()
            errors = StringIO()
            shell = Shell("test")
            success = run_script(shell, script, output, errors)
            self.assertTrue(success)
            self.assertIn("test$ ls file.txt", output.getvalue())
            self.assertIn("ls: file.txt", output.getvalue())
            self.assertEqual(errors.getvalue(), "")

    # Этап 2: ошибка скрипта сообщается.
    def test_script_error(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "start.txt"
            script.write_text("unknown\nexit\n", encoding="utf-8")
            output = StringIO()
            errors = StringIO()
            shell = Shell("test")
            success = run_script(shell, script, output, errors)
            self.assertTrue(success)
            self.assertIn("unknown: command not found", errors.getvalue())


class VfsTests(unittest.TestCase):
    """Проверки VFS этапа 3."""

    # Этап 3: JSON загружается в память.
    def test_load_json_vfs(self):
        data = {"docs": {"readme.txt": "hello"}, "empty": {}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.json"
            path.write_text(
                json.dumps(data), encoding="utf-8"
            )
            vfs = VirtualFileSystem.from_json(path)
            self.assertEqual(vfs.data, data)
            self.assertEqual(vfs.name, "nested")

    # Этап 3: отсутствующий JSON дает ошибку.
    def test_missing_vfs(self):
        with self.assertRaises(ShellError):
            VirtualFileSystem.from_json("missing.json")


class ReplTests(unittest.TestCase):
    """Проверка интерактивного цикла."""

    # Этап 1: REPL обрабатывает ввод и ошибки.
    def test_repl(self):
        shell = Shell("demo_vfs")
        commands = iter(["ls file.txt", "unknown", "exit"])
        prompts = []
        output = StringIO()
        errors = StringIO()

        def fake_input(prompt):
            prompts.append(prompt)
            return next(commands)

        from src.shell import repl

        self.assertEqual(repl(shell, fake_input, output, errors), 0)
        self.assertEqual(prompts, ["demo_vfs$ "] * 3)
        self.assertIn("ls: file.txt", output.getvalue())
        self.assertIn("unknown: command not found", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
