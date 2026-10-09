"""Эмулятор UNIX-подобной оболочки, вариант 16, этапы 1-2."""

import argparse
import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

EXIT_OK = 0
EXIT_SCRIPT_ERROR = 1
EXIT_FATAL = 2
COMMENT_PREFIX = "#"


class ShellError(Exception):
    """Ошибка выполнения команды."""


class ShellExit(Exception):
    """Сигнал штатного завершения оболочки."""


@dataclass
class Config:
    """Параметры командной строки."""

    vfs_path: str | None = None
    script_path: str | None = None


def build_prompt(vfs_name):
    """Возвращает приглашение оболочки."""
    return f"{vfs_name}$ "


def expand_variables(line):
    """Раскрывает переменные окружения реальной ОС."""
    return os.path.expandvars(line)


def parse_line(line):
    """Разбирает строку на имя команды и список аргументов."""
    try:
        parts = shlex.split(expand_variables(line))
    except ValueError as error:
        raise ShellError(f"parse: {error}") from error
    if not parts:
        return "", []
    return parts[0], parts[1:]


def require_args(command, args, minimum=None, maximum=None):
    """Проверяет допустимое количество аргументов."""
    if minimum is not None and len(args) < minimum:
        raise ShellError(f"{command}: missing arguments")
    if maximum is not None and len(args) > maximum:
        raise ShellError(f"{command}: too many arguments")


class Shell:
    """Состояние минимального REPL для первого этапа."""

    def __init__(self, vfs_name="vfs"):
        self.vfs_name = vfs_name
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }

    def cmd_ls(self, args):
        """Заглушка команды ls."""
        return f"ls: {' '.join(args)}" if args else "ls:"

    def cmd_cd(self, args):
        """Заглушка команды cd."""
        require_args("cd", args, maximum=1)
        return f"cd: {' '.join(args)}" if args else "cd:"

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
        """Выполняет одну строку пользовательского ввода."""
        command, args = parse_line(line)
        if not command:
            return None
        return self.execute(command, args)


def repl(shell, input_func=input, output_stream=sys.stdout,
         error_stream=sys.stderr):
    """Запускает интерактивный цикл оболочки."""
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


def print_config(config, output_stream):
    """Выводит заданные параметры запуска."""
    print(f"VFS path: {config.vfs_path or '<not set>'}", file=output_stream)
    print(
        f"Script path: {config.script_path or '<not set>'}",
        file=output_stream,
    )


def run_script(shell, script_path, output_stream, error_stream):
    """Выполняет стартовый скрипт и сообщает об ошибках выполнения."""
    path = Path(script_path)
    if not path.is_file():
        raise ShellError(f"script: file not found: {script_path}")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ShellError(f"script: read error: {error}") from error

    error_count = 0
    for number, line in enumerate(lines, start=1):
        command_line = line.strip()
        if not command_line or command_line.startswith(COMMENT_PREFIX):
            continue
        print(f"{build_prompt(shell.vfs_name)}{command_line}",
              file=output_stream)
        try:
            result = shell.run_line(command_line)
        except ShellExit:
            break
        except ShellError as error:
            print(f"script error (line {number}): {error}",
                  file=error_stream)
            error_count += 1
            continue
        if result is not None:
            print(result, file=output_stream)

    if error_count:
        print(f"script: finished with {error_count} error(s)",
              file=error_stream)
    return error_count == 0


def parse_arguments(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки")
    parser.add_argument("--vfs", help="путь к физическому расположению VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def vfs_name_from_path(vfs_path):
    """Возвращает имя VFS для приглашения к вводу."""
    return Path(vfs_path).stem if vfs_path else "vfs"


def main(argv=None):
    """Точка входа программы."""
    args = parse_arguments(argv)
    config = Config(vfs_path=args.vfs, script_path=args.script)
    print_config(config, sys.stdout)
    shell = Shell(vfs_name_from_path(config.vfs_path))

    if config.script_path:
        try:
            success = run_script(
                shell, config.script_path, sys.stdout, sys.stderr
            )
        except ShellError as error:
            print(error, file=sys.stderr)
            return EXIT_FATAL
        return EXIT_OK if success else EXIT_SCRIPT_ERROR

    return repl(shell)


if __name__ == "__main__":
    sys.exit(main())
