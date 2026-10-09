# Демонстрация — вариант 16

## Этап 1

```text
./run.sh
```

Показать `ls`, `cd`, `$HOME`, неизвестную команду, ошибку аргументов и `exit`.

## Этап 2

```text
./scripts/stage2_both.sh
./scripts/stage2_errors.sh
```

В начале выводятся пути VFS и скрипта. Затем показываются строки скрипта и
результаты. `stage2_errors.sh` показывает сообщения об ошибках выполнения
скрипта с номерами строк и коды возврата.

## Этап 3

```text
./scripts/stage3_minimal.sh
./scripts/stage3_files.sh
./scripts/stage3_nested.sh
./scripts/stage3_errors.sh
./scripts/stage3_all.sh
```

VFS берется из JSON в `vfs/base64/`, содержимое файлов закодировано в base64
и загружается в память. `stage3_all.sh` выполняет все команды всех этапов,
включая ошибки. `ls` и `cd` остаются заглушками до этапа 4.
