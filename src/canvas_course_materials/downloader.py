from pathlib import Path

import requests
from pathvalidate import sanitize_filename

from .state import load_state, save_state


def plan_downloads(
    files: list[dict], dest_dir: Path, state_path: Path, *, force: bool = False
) -> list[tuple[Path, dict]]:

    dest_dir.mkdir(parents=True, exist_ok=True)
    state = {} if force else load_state(state_path)
    plan: list[tuple[Path, dict]] = []
    for file in files:
        target = dest_dir / sanitize_filename(file["filename"])
        synced = state.get(str(file["id"])) == file["updated_at"]
        if force or not synced or not target.exists():
            plan.append((target, file))
    return plan


def download_files(
    session: requests.Session,
    plan: list[tuple[Path, dict]],
    state_path: Path,
    on_file=None,
) -> tuple[list[Path], list[str]]:

    state = load_state(state_path)
    downloaded: list[Path] = []
    errors: list[str] = []

    for target, file in plan:
        error: str | None = None
        try:
            _download(session, file["url"], target)
            state[str(file["id"])] = file["updated_at"]
            save_state(state_path, state)
            downloaded.append(target)
        except (requests.RequestException, OSError) as exc:
            error = f"{file['filename']}: {exc}"
            errors.append(error)

        if on_file is not None:
            on_file(file, target, error)

    return downloaded, errors


def _download(session: requests.Session, url: str, target: Path) -> None:
    tmp = target.with_suffix(target.suffix + ".part")
    try:
        with session.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with open(tmp, "wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 64):
                    fh.write(chunk)
        tmp.replace(target)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
