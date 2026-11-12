# Canvas LMS course-material downloader

A tool for downloading educational resources from a selected course in Canvas LMS.

## Features

- Pick a course interactively, or pass a course ID directly.
- Choose which files to download from an interactive file selector (with new/missing files pre-selected).
- Keeps track of downloaded files, so it only downloads new or updated files on the next run.
- Re-downloads files that are missing from your download folder.
- Supports `--dry-run`, `--force`, and `--all` for more control.
- All the files are downloaded to a new folder with the course's name inside your download directory.

## Installation

### Prerequisites
- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Git
- Canvas LMS API Access Token

### 1. Clone the repository
```bash
git clone https://github.com/JacobEscoto/canvas-course-materials
cd canvas-course-materials
```

### 2. Install dependencies
```bash
uv sync
```

## Usage

Run the tool with:

```bash
uv run canvas-materials
```

Some useful options:

- `--course ID` — download from a specific course without the interactive menu.
- `--dest DIR` — set a custom download destination.
- `--dry-run` — list what would be downloaded without saving anything.
- `--force` — re-download every file, even ones already up to date.
- `--all` — skip the file selector and download all new files.

## ⚙ Environment Configuration

To ensure the tool works perfectly, please create a `.env` file in the project root and follow this structure:

```env
CANVAS_URL=
CANVAS_TOKEN=
CANVAS_DOWNLOAD_DIR=
CANVAS_STATE_PATH=
```

- `CANVAS_URL` and `CANVAS_TOKEN` are required.
- `CANVAS_DOWNLOAD_DIR` is optional. If not set, files are downloaded to `~/Documents/Canvas` by default.
- `CANVAS_STATE_PATH` is optional. If not set, the download state is stored in your user data directory.

## License

[MIT](https://opensource.org/license/MIT)
