# AGENTS.md

## Project

Canvas LMS course-material downloader. Single-package uv project, src layout, Python >=3.14, build backend `uv_build`. No tests, no linter config, no CI.

## Commands

```bash
uv sync                              # install deps (also installs rich, requests, pathvalidate, ...)
uv run canvas-materials              # run the CLI (entrypoint: src/canvas_course_materials/__main__.py:main)
uv run canvas-materials --help       # flags: --course ID, --dest DIR, --dry-run, --force, --all, --version
```

No test suite exists. Verify changes manually:

```bash
uv run canvas-materials --course <ID> --dry-run   # reads the real Canvas API, writes nothing
uvx pyright --pythonpath .venv/bin/python src    # type check; bare `uvx pyright src` fails on imports
```

questionary widgets need a real TTY; to drive them in tests, pipe key bytes through a pty:
`script -qec "python3 <snippet>" /dev/null < <(printf '\x1b[B \r')` (arrow down, Space, Enter).

## Environment

- `.env` (gitignored) at repo root must define `CANVAS_URL` and `CANVAS_TOKEN`; optional `CANVAS_DOWNLOAD_DIR`, `CANVAS_STATE_PATH`. Missing/empty/invalid values raise `ConfigError` from `config.py` — never add fallbacks that skip this validation.
- Downloads and `state.json` live *outside* the repo by default (platformdirs: `~/Documents/Canvas`, user data dir). The `state.json` in the repo root is local noise, gitignored, not the one used at runtime.
- CLI commands hit the live Canvas API as the user's account. Never run the CLI without `--dry-run` when you only want to verify parsing/network code.
- State files are per-destination caches, NOT a record of where files are on disk. Never trust `state.json` alone to mean "the file exists"; `plan_downloads` must keep its `target.exists()` check. There can be several divergent state files (repo root + `platformdirs` user data dir) — only `CANVAS_STATE_PATH`/default decides which one is used.

## Conventions specific to this repo

- Errors are one-line Rich messages to stderr with exit codes (0 ok, 1 runtime/config, 2 usage, 130 = Ctrl+C/EOF). `main()` returns an int; never let exceptions print tracebacks (`KeyboardInterrupt` is caught in `__main__.py:main`).
- `downloader.py` separates `plan_downloads` (what needs downloading: stale per `state.json` file id → `updated_at`, **or** cached-but-missing on disk — deleted/moved files and changed `--dest` directories are re-downloaded) from `download_files`; `--dry-run` depends on this split. Per-file failures are collected in the errors list, not raised.
- Flow per run: course pick (`--course` or TUI select) → file selector (`cli.py:select_files`, questionary checkbox: Space toggles, Ctrl+A toggle-all, type to filter, Enter confirms; files needing download are pre-checked, `+`/`!` prefixes show new/missing status). `--all` skips the selector and is applied automatically when stdin is not a TTY (keeps scripted runs non-interactive). `--dry-run` bypasses selection entirely. Explicitly picking a file downloads it even if its status is "up to date"; `--all` respects `state.json` unless `--force`. Widget cancellation (Ctrl+C) → `KeyboardInterrupt` via `cli.py:_ask` → exit 130.
- All user-visible text imported from API data (course names, filenames) goes through `rich.markup.escape` — names contain characters Rich treats as markup.
- `.part` temp-file cleanup in `_download` must stay `except BaseException` — `KeyboardInterrupt` does not derive from `Exception`, and Ctrl+C mid-download must remove the temp file.
