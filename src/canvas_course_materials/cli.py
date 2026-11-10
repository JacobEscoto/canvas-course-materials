import argparse
import importlib.metadata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import questionary
from rich.console import Console


def _version() -> str:
    try:
        return importlib.metadata.version("canvas-course-materials")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


EX_CANCELLED = 130

STYLE = questionary.Style(
    [
        ("qmark", "fg:#5f87ff bold"),
        ("question", "bold"),
        ("answer", "fg:#5f87ff bold"),
        ("pointer", "fg:#5f87ff bold"),
        ("highlighted", "fg:#5f87ff bold"),
        ("checked", "fg:ansigreen"),
        ("selected", "fg:ansigreen"),
    ]
)


def _ask(question: questionary.Question) -> Any:
    try:
        return question.unsafe_ask()
    except KeyboardInterrupt, EOFError:
        raise KeyboardInterrupt from None


@dataclass(frozen=True)
class Args:
    course_id: int | None
    dest: Path | None
    dry_run: bool
    force: bool
    all_files: bool


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _directory(value: str) -> Path:
    path = Path(value).expanduser()
    if path.exists() and not path.is_dir():
        raise argparse.ArgumentTypeError(f"{path} exists but is not a directory")
    return path


def parse_args(argv: list[str] | None = None) -> Args:
    parser = argparse.ArgumentParser(
        prog="canvas-materials",
        description="Download the files of a Canvas LMS course to a folder.",
    )
    parser.add_argument(
        "--course",
        type=_positive_int,
        metavar="ID",
        help="Course ID. If skipped, an interactive menu is shown.",
    )
    parser.add_argument(
        "--dest",
        type=_directory,
        metavar="DIR",
        help="Download destination. Overrides CANVAS_DOWNLOAD_DIR.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be downloaded without saving anything.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download every file, even ones already up to date.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Skip the file selector and download all new files. "
        "This is automatic when stdin is not a terminal.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_version()}")
    ns = parser.parse_args(argv)
    return Args(
        course_id=ns.course,
        dest=ns.dest,
        dry_run=ns.dry_run,
        force=ns.force,
        all_files=ns.all,
    )


def ask_course(courses: list[dict]) -> dict:
    return _ask(
        questionary.select(
            "Course",
            choices=[
                questionary.Choice(
                    f"{course['id']:>7} · {course['name']}", value=course
                )
                for course in courses
            ],
            instruction="type to filter · ↑/↓ move · enter confirm · ctrl+c quit",
            use_jk_keys=False,
            use_search_filter=True,
            style=STYLE,
        )
    )


def select_files(
    files: list[dict],
    pending_ids: set[int],
    missing_ids: frozenset[int] | set[int] = frozenset(),
) -> list[dict]:
    console = Console()

    statuses = {
        file["id"]: (
            "missing"
            if file["id"] in missing_ids
            else "new"
            if file["id"] in pending_ids
            else "up to date"
        )
        for file in files
    }
    counts = Counter(statuses.values())

    console.print(
        f"[bold]{len(files)}[/bold] files \N{MIDDLE DOT} "
        f"[green]{counts['new']} new[/green] \N{MIDDLE DOT} "
        f"[yellow]{counts['missing']} missing[/yellow] \N{MIDDLE DOT} "
        f"[dim]{counts['up to date']} up to date[/dim]"
    )

    choices = []
    for file in files:
        status = statuses[file["id"]]
        prefix = "! " if status == "missing" else "+ " if status == "new" else "  "
        choices.append(
            questionary.Choice(
                prefix + file["filename"],
                value=file,
                checked=file["id"] in pending_ids,
            )
        )

    selected: list[dict] = _ask(
        questionary.checkbox(
            "Files to download",
            choices=choices,
            instruction="space toggle · ctrl+a all · type filter · enter confirm",
            use_jk_keys=False,
            use_search_filter=True,
            style=STYLE,
        )
    )
    return selected
