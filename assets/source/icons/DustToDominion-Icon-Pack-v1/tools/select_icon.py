"""Export one view under stable application filenames; never alters the game."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    views = {view["id"]: view for view in manifest["views"]}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("view", choices=views)
    parser.add_argument("--output", type=Path, required=True,
                        help="New output directory; must not already exist")
    args = parser.parse_args()
    hashes = dict(line.split("  ", 1)[::-1] for line in
                  (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines())
    view = views[args.view]
    exports = [(view["png"][str(size)], f"app-icon-{size}.png")
               for size in manifest["png_sizes"]]
    exports += [(view["icns"], "app-icon.icns"), (view["ico"], "app-icon.ico")]
    for relative, _ in exports:
        source = (root / relative).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            parser.error(f"Invalid or missing source: {relative}")
        if hashlib.sha256(source.read_bytes()).hexdigest() != hashes.get(relative):
            parser.error(f"Checksum mismatch: {relative}")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("Output already exists; choose a new directory.")
    output.mkdir(parents=True)
    for relative, name in exports:
        shutil.copy2(root / relative, output / name)
    selection = {"pack": manifest["name"], "version": manifest["version"],
                 "selected_view": args.view,
                 "files": [name for _, name in exports]}
    (output / "selection.json").write_text(json.dumps(selection, indent=2) + "\n",
                                            encoding="utf-8")
    print(f"Exported {args.view}: {output}")


if __name__ == "__main__":
    main()
