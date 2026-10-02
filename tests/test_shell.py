"""Тесты первого этапа эмулятора, вариант 16."""

import os
import unittest
from io import StringIO
from unittest.mock import patch

from src.shell import Shell, ShellError, ShellExit, build_prompt, parse_line


# Этап 1, пункты 2–3: prompt и переменные окружения.
# Код проверяет имя VFS в prompt и раскрытие переменной $HOME.
class ParserTests(unittest.TestCase):
    """Проверки prompt и парсера."""

    def test_prompt_contains_vfs_name(self):
        self.assertEqual(build_prompt("myvfs"), "myvfs$ ")

    def test_parse_line(self):
        self.assertEqual(parse_line("ls -l /tmp"), ("ls", ["-l", "/tmp"]))

    def test_environment_expansion(self):
        with patch.dict(os.environ, {"HOME": "/home/student"}):
            self.assertEqual(
                parse_line("ls $HOME"), ("ls", ["/home/student"])
            )


# Этап 1, пункты 4–6: команды и ошибки.
# Код проверяет заглушки ls/cd, ошибки и штатное завершение exit.
class CommandTests(unittest.TestCase):
    """Проверки команд первого этапа."""

    def setUp(self):
        self.shell = Shell("vfs16")

    def test_ls_stub(self):
        self.assertEqual(self.shell.run_line("ls /tmp -l"), "ls: /tmp -l")

    def test_cd_stub(self):
        self.assertEqual(self.shell.run_line("cd /home"), "cd: /home")

    def test_unknown_command(self):
        with self.assertRaises(ShellError):
            self.shell.run_line("unknown")

    def test_argument_error(self):
        with self.assertRaises(ShellError):
            self.shell.run_line("cd one two")

    def test_exit(self):
        with self.assertRaises(ShellExit):
            self.shell.run_line("exit")


# Этап 1, пункт 7: интерактивная демонстрация REPL.
# Код имитирует ввод пользователя и проверяет вывод команд и ошибок.
class ReplTests(unittest.TestCase):
    """Проверка интерактивного цикла."""

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

        self.assertEqual(
            repl(shell, fake_input, output, errors), 0
        )
        self.assertEqual(prompts, ["demo_vfs$ "] * 3)
        self.assertIn("ls: file.txt", output.getvalue())
        self.assertIn("unknown: command not found", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
