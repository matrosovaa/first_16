# Демонстрация Этапа 1

Запуск:

```text
./run.sh
```

Пример:

```text
vfs$ ls /tmp
ls: /tmp
vfs$ cd /home
cd: /home
vfs$ ls $HOME
ls: /Users/student  (пример; путь зависит от ОС и пользователя)
vfs$ unknown
unknown: command not found
vfs$ cd one two
cd: too many arguments
vfs$ exit
```

Здесь показаны CLI/REPL, prompt с именем VFS, раскрытие `$HOME`, заглушки
`ls` и `cd`, ошибка неизвестной команды, ошибка аргументов и `exit`.
