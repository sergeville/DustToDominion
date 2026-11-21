"""Verify the unpacked icon pack using only the Python standard library."""

from pathlib import Path
import hashlib
import sys


def verify(root: Path) -> list[str]:
    failures = []
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()):
            failures.append(f"Path outside package: {relative}")
        elif not path.is_file():
            failures.append(f"Missing: {relative}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(f"Hash mismatch: {relative}")
    return failures


if __name__ == "__main__":
    package = Path(__file__).resolve().parents[1]
    errors = verify(package)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    count = len((package / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines())
    print(f"PASS: {count} payload hashes verified.")
