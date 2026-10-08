"""Эмулятор оболочки, вариант 16, этапы 1-2."""

import argparse
import os
import shlex
import sys
from pathlib import Path

from dataclasses import dataclass


# Этап 1: код успешного завершения.
EXIT_OK = 0


class ShellError(Exception):
    """Ошибка команды или скрипта."""


class ShellExit(Exception):
    """Сигнал штатного завершения оболочки."""


# Этап 2: параметры запуска эмулятора.
@dataclass
class Config:
    """Параметры командной строки."""

    vfs_path: str | None = None
    script_path: str | None = None


# Этап 3: VFS должна храниться только в памяти.
# Этап 1: prompt содержит имя VFS.
def build_prompt(vfs_name):
    """Возвращает приглашение оболочки."""
    return f"{vfs_name}$ "


# Этап 1: раскрываем переменные окружения.
def expand_variables(line):
    """Раскрывает переменные окружения."""
    return os.path.expandvars(line)


# Этап 1: разбираем команду и аргументы.
def parse_line(line):
    """Разбирает строку на части."""

    try:
        parts = shlex.split(expand_variables(line))
    except ValueError as error:
        raise ShellError(f"parse: {error}") from error
    if not parts:
        return "", []
    return parts[0], parts[1:]


# Этап 1: проверяем количество аргументов.
def require_args(command, args, minimum=None, maximum=None):
    """Проверяет количество аргументов."""
    if minimum is not None and len(args) < minimum:
        raise ShellError(f"{command}: missing arguments")
    if maximum is not None and len(args) > maximum:
        raise ShellError(f"{command}: too many arguments")


class Shell:
    """Состояние REPL и подключенной VFS."""

    # Этап 3: VFS хранится в оболочке.
    def __init__(self, vfs_name="vfs", vfs=None):
        self.vfs_name = vfs_name
        self.vfs = vfs
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }

    # Этап 1: ls остается заглушкой до этапа 4.
    def cmd_ls(self, args):
        """Заглушка команды ls."""
        return f"ls: {' '.join(args)}" if args else "ls:"

    # Этап 1: cd остается заглушкой до этапа 4.
    def cmd_cd(self, args):
        """Заглушка команды cd."""
        require_args("cd", args, maximum=1)
        return f"cd: {' '.join(args)}" if args else "cd:"

    # Этап 1: exit завершает оболочку.
    def cmd_exit(self, args):
        """Завершает работу оболочки."""
        require_args("exit", args, maximum=0)
        raise ShellExit

    # Этап 1: неизвестная команда дает ошибку.
    def execute(self, command, args):
        """Выполняет распознанную команду."""
        handler = self.commands.get(command)
        if handler is None:
            raise ShellError(f"{command}: command not found")
        return handler(args)

    # Этап 1: выполняем одну строку ввода.
    def run_line(self, line):
        """Выполняет одну строку ввода."""
        command, args = parse_line(line)
        if not command:
            return None
        return self.execute(command, args)


# Этап 2: выводим параметры запуска.
def print_config(config, output_stream):
    """Показывает параметры запуска."""
    vfs_path = config.vfs_path or "<default>"
    script_path = config.script_path or "<interactive>"
    print(f"VFS path: {vfs_path}", file=output_stream)
    print(f"Script path: {script_path}", file=output_stream)


# Этап 2: выполняем команды скрипта.
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
        print(f"{build_prompt(shell.vfs_name)}{stripped}", file=output_stream)
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


# Этап 2: CLI получает пути VFS и скрипта.
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


# Этап 1: сохраняем интерактивный REPL.
def repl(shell, input_func=input, output_stream=sys.stdout,
         error_stream=sys.stderr):
    """Запускает интерактивный цикл."""
    prompt = build_prompt(shell.vfs_name)
    while True:
        try:
            line = input_func(prompt)
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


# Этап 2: запускаем скрипт или REPL.
def main(argv=None):
    """Точка входа программы."""
    args = parse_arguments(argv)
    config = Config(args.vfs, args.script)
    print_config(config, sys.stdout)
    vfs = None
    if config.vfs_path:
        from src.vfs import VirtualFileSystem

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
