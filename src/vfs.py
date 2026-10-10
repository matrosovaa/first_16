"""VFS для этапа 3, вариант 16."""

import json
import posixpath
from pathlib import Path

from src.errors import ShellError

ROOT = "/"
DIR_SIZE = 4096
DIR_MODE = 0o755
FILE_MODE = 0o644
MODE_MASK = 0o777


def is_dir(node):
    """Проверяет, что узел VFS является каталогом."""
    return isinstance(node, dict)


def validate_node(node, path):
    """Проверяет, что узел VFS - каталог или строка с содержимым."""
    if isinstance(node, str):
        return
    if not isinstance(node, dict):
        raise ShellError(f"vfs: invalid node: {path}")
    for name, child in node.items():
        validate_node(child, posixpath.join(path, name))


class VirtualFileSystem:
    """Хранит содержимое JSON-VFS в памяти."""

    def __init__(self, data, source_path):
        """Запоминает данные VFS и путь к исходному файлу."""
        self.data = data
        self.source_path = source_path
        self.modes = {}

    @classmethod
    def from_json(cls, path):
        """Создает VFS из JSON-файла."""
        file_path = Path(path)
        if not file_path.is_file():
            raise ShellError(f"vfs: file not found: {path}")
        try:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise ShellError(f"vfs: load error: {error}") from error
        if not isinstance(data, dict):
            raise ShellError("vfs: root must be a JSON object")
        validate_node(data, ROOT)
        return cls(data, str(file_path))

    @property
    def name(self):
        """Возвращает имя подключенной VFS."""
        return Path(self.source_path).stem

    def resolve(self, cwd, path):
        """Строит абсолютный нормализованный путь внутри VFS."""
        joined = posixpath.normpath(posixpath.join(cwd, path))
        return ROOT + joined.lstrip(ROOT)

    def lookup(self, path):
        """Возвращает узел по абсолютному пути или None."""
        node = self.data
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
        if is_dir(node):
            return DIR_SIZE
        return len(node.encode("utf-8"))

    def mode(self, path):
        """Возвращает права доступа узла."""
        if path in self.modes:
            return self.modes[path]
        return DIR_MODE if is_dir(self.lookup(path)) else FILE_MODE

    def set_mode(self, path, mode):
        """Меняет права узла только в памяти, не трогая данные VFS."""
        self.modes[path] = mode & MODE_MASK
