@echo off
if "%1"=="test" (
    python -m unittest discover -s tests -v
) else (
    python -m src.shell %*
)
