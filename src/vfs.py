"""VFS для этапа 3, вариант 16."""

import json
from pathlib import Path

from src.shell import ShellError


# Этап 3: загружаем JSON без распаковки на диск.
class VirtualFileSystem:
    """Хранит содержимое JSON-VFS в памяти."""

    def __init__(self, data, source_path):
        self.data = data
        self.source_path = source_path

    # Этап 3: JSON целиком загружается в память.
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
        return cls(data, str(file_path))

    # Этап 3: имя VFS берется из имени JSON-файла.
    @property
    def name(self):
        """Возвращает имя подключенной VFS."""
        return Path(self.source_path).stem
