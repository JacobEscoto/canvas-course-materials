import sys
from pathlib import Path

import requests
from pathvalidate import sanitize_filename
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from .cli import EX_CANCELLED, ask_course, parse_args, select_files
from .client import CanvasClient
from .config import ConfigError, load_config
from .courses import list_active_courses
from .downloader import download_files, plan_downloads
from .files import fetch_file_info
from .modules import list_module_file_ids
from .state import load_state

console = Console()
error_console = Console(stderr=True)

EX_OK = 0
EX_ERROR = 1


def main() -> int:
    try:
        return run()
    except KeyboardInterrupt:
        error_console.print("\n[yellow]Cancelled by user (Ctrl+C).[/yellow]")
        return EX_CANCELLED
    except EOFError:
        error_console.print("\n[yellow]Input closed, quitting.[/yellow]")
        return EX_CANCELLED
    except ConfigError as exc:
        error_console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        return EX_ERROR
    except requests.HTTPError as exc:
        response = exc.response
        status = response.status_code if response is not None else "?"
        if status == 401:
            error_console.print(
                "[bold red]Unauthorized (401).[/bold red] Your CANVAS_TOKEN seems invalid or expired."
            )
        else:
            url = response.url if response is not None else "<unknown>"
            error_console.print(
                f"[bold red]Canvas error:[/bold red] HTTP {status} from {url}"
            )
        return EX_ERROR
    except requests.RequestException as exc:
        error_console.print(f"[bold red]Network error:[/bold red] {exc}")
        return EX_ERROR


def run() -> int:
    args = parse_args()
    cfg = load_config()
    download_dir = args.dest if args.dest is not None else cfg.download_dir

    client = CanvasClient(cfg.base_url, cfg.token)
    console.print(f"[dim]Connecting to {escape(cfg.base_url)} ...[/dim]")
    courses = list_active_courses(client)

    if not courses:
        console.print("[yellow]Could not find active courses.[/yellow]")
        return EX_OK

    if args.course_id is None:
        course = ask_course(courses)
    else:
        course = next((c for c in courses if c["id"] == args.course_id), None)
        if course is None:
            error_console.print(
                f"[bold red]Course {args.course_id} is not one of your active courses.[/bold red]\n"
                f"Available IDs: {_format_ids(courses)}\n"
                f"Tip: run [bold]canvas-materials[/bold] without --course to see the full menu."
            )
            return EX_ERROR

    course_dir = download_dir / sanitize_filename(course["name"])

    console.print(
        Panel.fit(
            f"[bold]{escape(course['name'])}[/bold] [dim](ID {course['id']})[/dim]\n"
            f"[dim]Destination:[/dim] {escape(str(course_dir))}",
            title="Synchronizing",
        )
    )

    console.print("[dim]Reading modules ...[/dim]")
    file_ids = list_module_file_ids(client, course["id"])
    infos = [fetch_file_info(client, course["id"], fid) for fid in file_ids]
    files = [i for i in infos if i is not None]
    blocked = len(infos) - len(files)

    plan = plan_downloads(files, course_dir, cfg.state_path, force=args.force)

    if args.dry_run:
        table = Table(
            title=f"{len(plan)} file(s) would be downloaded", title_justify="left"
        )
        table.add_column("File", style="cyan")
        for target, _ in plan:
            table.add_row(escape(target.name))
        console.print(table)
        console.print(f"[dim]Would write to:[/dim] {escape(str(course_dir))}")
        return EX_OK

    if not plan:
        console.print(
            Panel.fit(
                f"[green]Everything is up to date.[/green]\n"
                f"{len(files)} accessible · {blocked} blocked · 0 new\n"
                f"[dim]Tip: use --force to re-download everything.[/dim]",
                title="Sync complete",
            )
        )
        return EX_OK

    if args.all_files or not sys.stdin.isatty():
        pairs_to_download = plan
    else:
        state = load_state(cfg.state_path)
        missing_ids = {
            file["id"]
            for _, file in plan
            if state.get(str(file["id"])) == file["updated_at"]
        }
        chosen = select_files(files, {file["id"] for _, file in plan}, missing_ids)
        if not chosen:
            console.print("[yellow]Nothing selected, nothing to download.[/yellow]")
            return EX_OK
        pairs_to_download = [
            (course_dir / sanitize_filename(file["filename"]), file) for file in chosen
        ]

    console.print(f"[dim]Downloading {len(pairs_to_download)} file(s) ...[/dim]")
    progress = Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )
    with progress:
        task = progress.add_task("Downloading", total=len(pairs_to_download))
        downloaded, errors = download_files(
            client.session,
            pairs_to_download,
            cfg.state_path,
            on_file=lambda file, target, exc: _on_file(
                progress, task, file, target, exc
            ),
        )

    failed = f" · [red]{len(errors)} failed[/red]" if errors else ""
    console.print(
        Panel.fit(
            f"[green]{len(downloaded)} new file(s)[/green] in {escape(str(course_dir))}\n"
            f"{len(files)} accessible · {blocked} blocked{failed}",
            title="Sync complete",
        )
    )
    for message in errors:
        console.print(f"  [red]·[/red] {message}")
    return EX_OK


def _on_file(
    progress: Progress, task_id, _file: dict, target: Path, error: str | None
) -> None:
    if error is None:
        progress.console.print(f"  [green]OK[/green] {escape(target.name)}")
    else:
        progress.console.print(f"  [red]X[/red] {escape(target.name)}")
        error_console.print(f"    [red]{escape(str(error))}[/red]")
    progress.advance(task_id)


def _format_ids(courses: list[dict], limit: int = 10) -> str:
    ids = [str(c["id"]) for c in courses[:limit]]
    if len(courses) > limit:
        ids.append("...")
    return ", ".join(ids)


if __name__ == "__main__":
    sys.exit(main())
