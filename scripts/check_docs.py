#!/usr/bin/env python3

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_PATHS = (
    (
        "Windows",
        re.compile(
            r"(?:^|[^A-Za-z0-9])[A-Z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+[\\/]+",
            re.IGNORECASE,
        ),
    ),
    ("macOS", re.compile(r"/Users/[A-Za-z0-9._-]+/")),
    ("Linux", re.compile(r"/home/[A-Za-z0-9._-]+/")),
)
LEGACY_HOSTS = ("platform-web-vue", "platform-api-v2")
HISTORICAL_PREFIXES = (
    ".omx/",
    "archive/",
    "docs/CHANGELOG.md",
    "docs/archive/",
    "docs/releases/",
    "apps/platform-api/docs/archive/",
)


def markdown_files() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.md",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = (ROOT / name for name in result.stdout.splitlines() if name)
    return [path for path in paths if path.is_file()]


def is_historical(path: Path, text: str) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    header = "\n".join(text.splitlines()[:12])
    return relative.startswith(HISTORICAL_PREFIXES) or any(
        marker in header
        for marker in (
            "Status: Archived",
            "状态：Archived",
            "状态： Archived",
        )
    )


def local_path_kind(line: str) -> str | None:
    for kind, pattern in LOCAL_PATHS:
        if pattern.search(line):
            return kind
    return None


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT).as_posix()
    errors: list[str] = []

    if is_historical(path, text):
        return errors

    for line_number, line in enumerate(text.splitlines(), start=1):
        path_kind = local_path_kind(line)
        if path_kind:
            errors.append(
                f"{relative}:{line_number}: {path_kind} local absolute path"
            )
        for legacy_host in LEGACY_HOSTS:
            if legacy_host in line:
                errors.append(
                    f"{relative}:{line_number}: retired host name {legacy_host}"
                )
    return errors


def self_check() -> None:
    assert local_path_kind("/Users/alice/project/readme.md") == "macOS"
    assert local_path_kind("/home/alice/project/readme.md") == "Linux"
    assert local_path_kind(r"C:\Users\alice\project\readme.md") == "Windows"
    assert local_path_kind("C:/Users/alice/project/readme.md") == "Windows"
    assert local_path_kind("Path: C:/Users/alice/project/readme.md") == "Windows"
    assert local_path_kind("/Users/<name>/project") is None
    assert local_path_kind("/home/<name>/project") is None
    assert local_path_kind(r"C:\Users\<name>\project") is None
    assert is_historical(
        ROOT / "docs/archive/example.md",
        "# Example\n\n> Status: Archived.",
    )
    assert not is_historical(
        ROOT / "docs/quickstart/local-dev.md",
        "# Example\n\n- Status: Active",
    )


def main() -> int:
    self_check()
    errors = [error for path in markdown_files() for error in check_file(path)]
    if errors:
        print("\n".join(errors))
        return 1
    print("Documentation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
