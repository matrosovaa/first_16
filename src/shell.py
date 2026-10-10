"""Эмулятор оболочки, вариант 16, этапы 1-5."""

import argparse
import os
import shlex
import sys
from pathlib import Path

from dataclasses import dataclass
from datetime import datetime

from src.commands import (
    require_args,
    run_cd,
    run_chmod,
    run_date,
    run_find,
    run_ls,
)
from src.errors import ShellError, ShellExit
from src.vfs import ROOT, VirtualFileSystem


EXIT_OK = 0


@dataclass
class Config:
    """Параметры командной строки."""

    vfs_path: str | None = None
    script_path: str | None = None


def build_prompt(vfs_name, cwd=None):
    """Возвращает приглашение оболочки."""
    if cwd is None:
        return f"{vfs_name}$ "
    return f"{vfs_name}:{cwd}$ "


def current_time():
    """Возвращает текущее время с часовым поясом."""
    return datetime.now().astimezone()


def expand_variables(line):
    """Раскрывает переменные окружения."""
    return os.path.expandvars(line)


def parse_line(line):
    """Разбирает строку на части."""

    try:
        parts = shlex.split(expand_variables(line))
    except ValueError as error:
        raise ShellError(f"parse: {error}") from error
    if not parts:
        return "", []
    return parts[0], parts[1:]


class Shell:
    """Состояние REPL и подключенной VFS."""

    def __init__(self, vfs_name="vfs", vfs=None, clock=current_time):
        """Создает оболочку с VFS, текущим каталогом и командами."""
        self.vfs_name = vfs_name
        if vfs is None:
            vfs = VirtualFileSystem({}, vfs_name)
        self.vfs = vfs
        self.cwd = ROOT
        self.clock = clock
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "date": self.cmd_date,
            "find": self.cmd_find,
            "chmod": self.cmd_chmod,
            "exit": self.cmd_exit,
        }

    def prompt(self):
        """Возвращает приглашение с именем VFS и текущим каталогом."""
        return build_prompt(self.vfs_name, self.cwd)

    def cmd_ls(self, args):
        """Показывает содержимое каталога или файл."""
        return run_ls(self.vfs, self.cwd, args)

    def cmd_cd(self, args):
        """Меняет текущий каталог."""
        self.cwd = run_cd(self.vfs, self.cwd, args)

    def cmd_date(self, args):
        """Показывает текущие дату и время."""
        return run_date(self.clock(), args)

    def cmd_find(self, args):
        """Ищет файлы и каталоги в VFS."""
        return run_find(self.vfs, self.cwd, args)

    def cmd_chmod(self, args):
        """Меняет права доступа к файлам и каталогам в памяти."""
        run_chmod(self.vfs, self.cwd, args)

    def cmd_exit(self, args):
        """Завершает работу оболочки."""
        require_args("exit", args, maximum=0)
        raise ShellExit

    def execute(self, command, args):
        """Выполняет распознанную команду."""
        handler = self.commands.get(command)
        if handler is None:
            raise ShellError(f"{command}: command not found")
        return handler(args)

    def run_line(self, line):
        """Выполняет одну строку ввода."""
        command, args = parse_line(line)
        if not command:
            return None
        return self.execute(command, args)


def print_config(config, output_stream):
    """Показывает параметры запуска."""
    vfs_path = config.vfs_path or "<default>"
    script_path = config.script_path or "<interactive>"
    print(f"VFS path: {vfs_path}", file=output_stream)
    print(f"Script path: {script_path}", file=output_stream)


def run_script(shell, script_path, output_stream, error_stream):
    """Выполняет команды скрипта."""

    path = Path(script_path)
    if not path.is_file():
        raise ShellError(f"script: file not found: {script_path}")

    had_error = False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ShellError(f"script: read error: {error}") from error

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        print(f"{shell.prompt()}{stripped}", file=output_stream)
        try:
            result = shell.run_line(stripped)
        except ShellExit:
            break
        except ShellError as error:
            print(error, file=error_stream)
            had_error = True
            continue
        if result is not None:
            print(result, file=output_stream)
    return True


def parse_arguments(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки, вариант 16"
    )
    parser.add_argument("--vfs", help="путь к JSON-файлу VFS")
    parser.add_argument(
        "--script", help="путь к стартовому скрипту"
    )
    return parser.parse_args(argv)


def repl(shell, input_func=input, output_stream=sys.stdout,
         error_stream=sys.stderr):
    """Запускает интерактивный цикл."""
    while True:
        try:
            line = input_func(shell.prompt())
        except EOFError:
            print(file=output_stream)
            break
        except KeyboardInterrupt:
            print(file=output_stream)
            continue
        try:
            result = shell.run_line(line)
        except ShellExit:
            break
        except ShellError as error:
            print(error, file=error_stream)
            continue
        if result is not None:
            print(result, file=output_stream)
    return EXIT_OK


def main(argv=None):
    """Точка входа программы."""
    args = parse_arguments(argv)
    config = Config(args.vfs, args.script)
    print_config(config, sys.stdout)
    vfs = None
    if config.vfs_path:
        vfs = VirtualFileSystem.from_json(config.vfs_path)
    vfs_name = vfs.name if vfs is not None else "vfs"
    shell = Shell(vfs_name, vfs)

    if config.script_path:
        success = run_script(
            shell, config.script_path, sys.stdout, sys.stderr
        )
        return EXIT_OK if success else 1

    return repl(shell)

if __name__ == "__main__":
    sys.exit(main())
