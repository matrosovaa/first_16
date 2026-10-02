"""Эмулятор UNIX-подобной оболочки, вариант 16, этап 1."""

import os
import shlex
import sys

EXIT_OK = 0


class ShellError(Exception):
    """Ошибка выполнения команды."""


class ShellExit(Exception):
    """Сигнал штатного завершения оболочки."""


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


def main():
    """Точка входа программы."""
    shell = Shell("vfs")
    return repl(shell)


if __name__ == "__main__":
    sys.exit(main())
