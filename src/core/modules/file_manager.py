from pathlib import Path
from datetime import datetime

ROOT = (Path.home() / "storage" / "shared").resolve()


def get_directory(relative_path="."):
    target = (ROOT / relative_path).resolve()

    if not target.is_relative_to(ROOT):
        raise PermissionError("Accès refusé")

    if not target.is_dir():
        raise NotADirectoryError("Dossier introuvable")

    return target


def list_files(relative_path="."):
    directory = get_directory(relative_path)
    results = []

    for item in directory.iterdir():
        try:
            if item.is_symlink():
                continue

            info = item.stat()

            results.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": info.st_size,
                "modified": datetime.fromtimestamp(
                    info.st_mtime
                ).isoformat()
            })

        except (PermissionError, OSError):
            continue

    results.sort(
        key=lambda x: (
            x["type"] != "directory",
            x["name"].lower()
        )
    )

    return {
        "path": str(directory.relative_to(ROOT)),
        "count": len(results),
        "items": results
    }
