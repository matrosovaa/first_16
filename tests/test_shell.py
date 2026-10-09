"""Тесты этапов 1-2 эмулятора, вариант 16."""

import os
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src.shell import (
    EXIT_FATAL,
    EXIT_OK,
    EXIT_SCRIPT_ERROR,
    Config,
    Shell,
    ShellError,
    ShellExit,
    build_prompt,
    main,
    parse_arguments,
    parse_line,
    print_config,
    repl,
    run_script,
    vfs_name_from_path,
)


def write_script(directory, text):
    path = Path(directory) / "start.txt"
    path.write_text(text, encoding="utf-8")
    return path


class ParserTests(unittest.TestCase):
    def test_prompt_contains_vfs_name(self):
        self.assertEqual(build_prompt("myvfs"), "myvfs$ ")

    def test_parse_line(self):
        self.assertEqual(parse_line("ls -l /tmp"), ("ls", ["-l", "/tmp"]))

    def test_environment_expansion(self):
        with patch.dict(os.environ, {"HOME": "/home/student"}):
            self.assertEqual(
                parse_line("ls $HOME"), ("ls", ["/home/student"])
            )


class CommandTests(unittest.TestCase):
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


class ReplTests(unittest.TestCase):
    def test_repl(self):
        shell = Shell("demo_vfs")
        commands = iter(["ls file.txt", "unknown", "exit"])
        prompts = []
        output = StringIO()
        errors = StringIO()

        def fake_input(prompt):
            prompts.append(prompt)
            return next(commands)

        self.assertEqual(repl(shell, fake_input, output, errors), EXIT_OK)
        self.assertEqual(prompts, ["demo_vfs$ "] * 3)
        self.assertIn("ls: file.txt", output.getvalue())
        self.assertIn("unknown: command not found", errors.getvalue())


class ConfigTests(unittest.TestCase):
    def test_parse_arguments(self):
        args = parse_arguments(["--vfs", "a.json", "--script", "b.txt"])
        self.assertEqual((args.vfs, args.script), ("a.json", "b.txt"))

    def test_parse_arguments_defaults(self):
        args = parse_arguments([])
        self.assertEqual((args.vfs, args.script), (None, None))

    def test_print_config(self):
        output = StringIO()
        print_config(Config("vfs/test.json", "scripts/test.txt"), output)
        self.assertIn("VFS path: vfs/test.json", output.getvalue())
        self.assertIn("Script path: scripts/test.txt", output.getvalue())

    def test_print_config_not_set(self):
        output = StringIO()
        print_config(Config(), output)
        self.assertIn("VFS path: <not set>", output.getvalue())
        self.assertIn("Script path: <not set>", output.getvalue())

    def test_vfs_name_from_path(self):
        self.assertEqual(vfs_name_from_path("vfs/minimal.json"), "minimal")
        self.assertEqual(vfs_name_from_path(None), "vfs")


class ScriptTests(unittest.TestCase):
    def run_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            script = write_script(directory, text)
            output = StringIO()
            errors = StringIO()
            success = run_script(Shell("test"), script, output, errors)
        return success, output.getvalue(), errors.getvalue()

    def test_comments_and_output(self):
        success, output, errors = self.run_text(
            "# comment\nls file.txt\nexit\n"
        )
        self.assertTrue(success)
        self.assertNotIn("comment", output)
        self.assertIn("test$ ls file.txt", output)
        self.assertIn("ls: file.txt", output)
        self.assertEqual(errors, "")

    def test_exit_stops_script(self):
        _, output, _ = self.run_text("exit\nls after\n")
        self.assertNotIn("after", output)

    def test_error_is_reported_with_line_number(self):
        success, output, errors = self.run_text("ls\nunknown\nexit\n")
        self.assertFalse(success)
        self.assertIn("test$ unknown", output)
        self.assertIn(
            "script error (line 2): unknown: command not found", errors
        )
        self.assertIn("script: finished with 1 error(s)", errors)

    def test_script_continues_after_error(self):
        _, output, _ = self.run_text("unknown\nls ok\n")
        self.assertIn("ls: ok", output)

    def test_missing_script(self):
        with self.assertRaises(ShellError):
            run_script(Shell("test"), "missing.txt", StringIO(), StringIO())


class MainTests(unittest.TestCase):
    def run_main(self, text=None, script_path=None):
        output = StringIO()
        errors = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            if text is not None:
                script_path = str(write_script(directory, text))
            argv = ["--vfs", "vfs/demo.json"]
            if script_path:
                argv += ["--script", script_path]
            with patch("sys.stdout", output), patch("sys.stderr", errors):
                code = main(argv)
        return code, output.getvalue(), errors.getvalue()

    def test_parameters_are_printed(self):
        _, output, _ = self.run_main("exit\n")
        self.assertIn("VFS path: vfs/demo.json", output)
        self.assertIn("Script path:", output)

    def test_success_exit_code(self):
        code, _, _ = self.run_main("ls\nexit\n")
        self.assertEqual(code, EXIT_OK)

    def test_script_error_exit_code(self):
        code, _, errors = self.run_main("unknown\n")
        self.assertEqual(code, EXIT_SCRIPT_ERROR)
        self.assertIn("command not found", errors)

    def test_missing_script_is_reported_without_traceback(self):
        code, _, errors = self.run_main(script_path="missing.txt")
        self.assertEqual(code, EXIT_FATAL)
        self.assertIn("script: file not found: missing.txt", errors)


if __name__ == "__main__":
    unittest.main()
