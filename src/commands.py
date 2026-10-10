"""Логика команд ls, cd, find, date и chmod, вариант 16."""

import fnmatch
import posixpath
import re

from src.errors import ShellError
from src.vfs import MODE_MASK, ROOT, is_dir

CURRENT_DIR = "."
DATE_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
DATE_PREFIX = "+"
PERMISSION_CHARS = "rwxrwxrwx"
FIND_PREDICATES = ("-name", "-type")
FIND_TYPES = {"f": False, "d": True}
OCTAL_PATTERN = re.compile(r"[0-7]{1,4}")
CLAUSE_PATTERN = re.compile(r"([ugoa]*)([-+=])([rwx]*)")
WHO_SHIFTS = {"u": 6, "g": 3, "o": 0}
PERMISSION_VALUES = {"r": 4, "w": 2, "x": 1}
PERMISSION_MASK = 0o7
RECURSIVE_OPTION = "-R"


def require_args(command, args, minimum=None, maximum=None):
    """Проверяет количество аргументов."""
    if minimum is not None and len(args) < minimum:
        raise ShellError(f"{command}: missing arguments")
    if maximum is not None and len(args) > maximum:
        raise ShellError(f"{command}: too many arguments")


def split_options(command, args, allowed):
    """Отделяет короткие опции вида -l от остальных аргументов."""
    flags = set()
    operands = []
    options_done = False
    for arg in args:
        if options_done or arg == "-" or not arg.startswith("-"):
            operands.append(arg)
        elif arg == "--":
            options_done = True
        else:
            flags.update(check_letters(command, arg[1:], allowed))
    return flags, operands


def check_letters(command, letters, allowed):
    """Проверяет, что все буквы опции поддерживаются командой."""
    for letter in letters:
        if letter not in allowed:
            raise ShellError(f"{command}: invalid option -- '{letter}'")
    return set(letters)


def format_mode(directory, mode):
    """Строит строку прав в стиле ls -l, например drwxr-xr-x."""
    kind = "d" if directory else "-"
    total = len(PERMISSION_CHARS)
    bits = [
        char if mode & (1 << (total - 1 - index)) else "-"
        for index, char in enumerate(PERMISSION_CHARS)
    ]
    return kind + "".join(bits)


def format_entry(vfs, path, label, long_format):
    """Форматирует одну строку вывода ls."""
    if not long_format:
        return label
    mode = format_mode(is_dir(vfs.lookup(path)), vfs.mode(path))
    return f"{mode} {vfs.size(path):>6} {label}"


def run_ls(vfs, cwd, args):
    """Выполняет ls [-l] [путь]."""
    flags, operands = split_options("ls", args, "l")
    require_args("ls", operands, maximum=1)
    target = operands[0] if operands else CURRENT_DIR
    path = vfs.resolve(cwd, target)
    node = vfs.lookup(path)
    if node is None:
        raise ShellError(
            f"ls: cannot access '{target}': No such file or directory"
        )
    if is_dir(node):
        entries = [(posixpath.join(path, name), name) for name in sorted(node)]
    else:
        entries = [(path, target)]
    lines = [format_entry(vfs, *entry, "l" in flags) for entry in entries]
    return "\n".join(lines) or None


def run_cd(vfs, cwd, args):
    """Выполняет cd [путь] и возвращает новый текущий каталог."""
    require_args("cd", args, maximum=1)
    target = args[0] if args else ROOT
    path = vfs.resolve(cwd, target)
    node = vfs.lookup(path)
    if node is None:
        raise ShellError(f"cd: {target}: No such file or directory")
    if not is_dir(node):
        raise ShellError(f"cd: {target}: Not a directory")
    return path


def run_date(now, args):
    """Выполняет date [+формат]."""
    require_args("date", args, maximum=1)
    if not args:
        return now.strftime(DATE_FORMAT)
    if not args[0].startswith(DATE_PREFIX):
        raise ShellError(f"date: invalid date '{args[0]}'")
    return now.strftime(args[0].removeprefix(DATE_PREFIX))


def parse_find(args):
    """Разбирает аргументы find: пути, -name и -type."""
    index = 0
    while index < len(args) and not args[index].startswith("-"):
        index += 1
    paths = args[:index] or [CURRENT_DIR]
    options = {}
    while index < len(args):
        predicate = args[index]
        if predicate not in FIND_PREDICATES:
            raise ShellError(f"find: unknown predicate `{predicate}'")
        value = args[index + 1:index + 2]
        if not value:
            raise ShellError(f"find: missing argument to `{predicate}'")
        options[predicate] = value[0]
        index += 2
    return paths, options.get("-name"), options.get("-type")


def matches(path, node, name, kind):
    """Проверяет узел на соответствие условиям -name и -type."""
    if kind is not None and FIND_TYPES[kind] != is_dir(node):
        return False
    base = posixpath.basename(path) or ROOT
    return name is None or fnmatch.fnmatchcase(base, name)


def display_path(target, start, path):
    """Строит путь для вывода так, как его ввел пользователь."""
    relative = posixpath.relpath(path, start)
    if relative == CURRENT_DIR:
        return target
    return posixpath.join(target, relative)


def find_in(vfs, cwd, target, name, kind):
    """Ищет узлы внутри одного начального пути."""
    start = vfs.resolve(cwd, target)
    if vfs.lookup(start) is None:
        raise ShellError(f"find: '{target}': No such file or directory")
    return [
        display_path(target, start, path)
        for path, node in vfs.walk(start)
        if matches(path, node, name, kind)
    ]


def run_find(vfs, cwd, args):
    """Выполняет find [путь...] [-name шаблон] [-type f|d]."""
    paths, name, kind = parse_find(args)
    if kind is not None and kind not in FIND_TYPES:
        raise ShellError(f"find: Unknown argument to -type: {kind}")
    lines = []
    for target in paths:
        lines.extend(find_in(vfs, cwd, target, name, kind))
    return "\n".join(lines) or None


def parse_clause(part, text):
    """Разбирает одну символьную часть режима, например u+x."""
    match = CLAUSE_PATTERN.fullmatch(part)
    if match is None:
        raise ShellError(f"chmod: invalid mode: '{text}'")
    who, operator, letters = match.groups()
    shifts = {WHO_SHIFTS[letter] for letter in who.replace("a", "ugo")}
    shifts = shifts or set(WHO_SHIFTS.values())
    value = sum(PERMISSION_VALUES[letter] for letter in set(letters))
    who_mask = sum(PERMISSION_MASK << shift for shift in shifts)
    bits = sum(value << shift for shift in shifts)
    return who_mask, operator, bits


def apply_clause(current, clause):
    """Применяет разобранную часть режима к текущим правам."""
    who_mask, operator, bits = clause
    if operator == "+":
        return current | bits
    if operator == "-":
        return current & ~bits
    return (current & ~who_mask) | bits


def parse_mode(text):
    """Возвращает функцию, которая считает новые права по старым."""
    if OCTAL_PATTERN.fullmatch(text):
        value = int(text, 8)
        if value > MODE_MASK:
            raise ShellError(f"chmod: invalid mode: '{text}'")
        return lambda current: value
    clauses = [parse_clause(part, text) for part in text.split(",")]

    def change(current):
        """Применяет все части режима по порядку."""
        for clause in clauses:
            current = apply_clause(current, clause)
        return current

    return change


def chmod_target(vfs, path, change, recursive):
    """Меняет права узла и, при -R, всех его потомков."""
    paths = [item for item, _ in vfs.walk(path)] if recursive else [path]
    for item in paths:
        vfs.set_mode(item, change(vfs.mode(item)))


def run_chmod(vfs, cwd, args):
    """Выполняет chmod [-R] режим путь..."""
    recursive = RECURSIVE_OPTION in args
    operands = [arg for arg in args if arg != RECURSIVE_OPTION]
    if not operands:
        raise ShellError("chmod: missing operand")
    mode_text, targets = operands[0], operands[1:]
    if not targets:
        raise ShellError(f"chmod: missing operand after '{mode_text}'")
    change = parse_mode(mode_text)
    errors = []
    for target in targets:
        path = vfs.resolve(cwd, target)
        if vfs.lookup(path) is None:
            errors.append(
                f"chmod: cannot access '{target}': No such file or directory"
            )
            continue
        chmod_target(vfs, path, change, recursive)
    if errors:
        raise ShellError("\n".join(errors))
