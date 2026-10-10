"""Виртуальная файловая система из JSON-файла, этап 3."""

import base64
import binascii
import json
import posixpath
from pathlib import Path

from src.errors import ShellError

ROOT = "/"
DIR_SIZE = 4096
DIR_MODE = 0o755
FILE_MODE = 0o644


def is_dir(node):
    """Проверяет, что узел VFS является каталогом."""
    return isinstance(node, dict)


def decode_node(node, location):
    """Рекурсивно превращает JSON-узел в каталог (dict) или файл (bytes)."""
    if isinstance(node, dict):
        return {
            name: decode_node(child, f"{location}/{name}")
            for name, child in node.items()
        }
    if isinstance(node, str):
        try:
            return base64.b64decode(node, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ShellError(
                f"vfs: invalid base64 in {location}: {error}"
            ) from error
    raise ShellError(
        f"vfs: unsupported value in {location}: {type(node).__name__}"
    )


class VirtualFileSystem:
    """Хранит дерево VFS только в памяти."""

    def __init__(self, root, source_path):
        self.root = root
        self.source_path = str(source_path)

    @classmethod
    def from_json(cls, path):
        """Читает JSON-файл целиком; исходный файл не изменяется."""
        file_path = Path(path)
        if not file_path.is_file():
            raise ShellError(f"vfs: file not found: {path}")
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ShellError(f"vfs: load error: {error}") from error
        if not isinstance(raw, dict):
            raise ShellError("vfs: root must be a JSON object")
        return cls(decode_node(raw, ""), file_path)

    @property
    def name(self):
        """Имя VFS берется из имени JSON-файла."""
        return Path(self.source_path).stem

    def resolve(self, cwd, path):
        """Строит абсолютный нормализованный путь внутри VFS."""
        joined = posixpath.normpath(posixpath.join(cwd, path))
        return ROOT + joined.lstrip(ROOT)

    def lookup(self, path):
        """Возвращает узел по абсолютному пути или None."""
        node = self.root
        for part in path.split(ROOT):
            if not part:
                continue
            if not is_dir(node) or part not in node:
                return None
            node = node[part]
        return node

    def walk(self, path):
        """Обходит узел и всех его потомков в алфавитном порядке."""
        node = self.lookup(path)
        yield path, node
        if is_dir(node):
            for name in sorted(node):
                yield from self.walk(posixpath.join(path, name))

    def size(self, path):
        """Возвращает размер узла в байтах."""
        node = self.lookup(path)
        return DIR_SIZE if is_dir(node) else len(node)

    def mode(self, path):
        """Возвращает права доступа узла."""
        return DIR_MODE if is_dir(self.lookup(path)) else FILE_MODE
