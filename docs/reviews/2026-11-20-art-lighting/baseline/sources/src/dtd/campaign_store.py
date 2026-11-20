"""Validated station checkpoints, separate from game settings (spec 19)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from dtd.campaign import Campaign
from dtd.persistence import resolve_persistence_dir


SAVE_VERSION = 1
MAX_SAVE_BYTES = 64 * 1024


class SaveError(Exception):
    """A checkpoint could not be read or safely written; play can continue."""


def _reject_constant(value: str) -> Any:
    raise ValueError(f"nonfinite JSON number: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


class CampaignStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else resolve_persistence_dir() / "campaign.json"

    def exists(self) -> bool:
        """Also surface unreadable/dangling checkpoints for explicit replacement."""
        try:
            self.path.lstat()
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise SaveError("Could not inspect the saved campaign.") from exc

    def load(self) -> Campaign:
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_SAVE_BYTES + 1)
            if len(raw) > MAX_SAVE_BYTES:
                raise ValueError("campaign file exceeds the size limit")
            envelope = json.loads(
                raw.decode("utf-8"),
                parse_constant=_reject_constant,
                object_pairs_hook=_unique_object,
            )
            if not isinstance(envelope, dict) or set(envelope) != {"version", "campaign"}:
                raise ValueError("invalid checkpoint envelope")
            if type(envelope["version"]) is not int or envelope["version"] != SAVE_VERSION:
                raise ValueError("unsupported checkpoint version")
            if not isinstance(envelope["campaign"], dict):
                raise ValueError("invalid campaign payload")
            return Campaign.from_dict(envelope["campaign"])
        except (OSError, ValueError, TypeError, OverflowError, RecursionError) as exc:
            raise SaveError("Could not load the saved campaign; its file was preserved.") from exc

    def save(self, campaign: Campaign) -> None:
        """Validate before touching disk and replace only a fully flushed file."""
        temporary: Path | None = None
        try:
            payload = campaign.to_dict()
            Campaign.from_dict(payload)
            raw = (json.dumps(
                {"version": SAVE_VERSION, "campaign": payload},
                allow_nan=False, ensure_ascii=False, indent=2,
            ) + "\n").encode("utf-8")
            if len(raw) > MAX_SAVE_BYTES:
                raise ValueError("campaign exceeds the size limit")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=self.path.parent,
                prefix=f".{self.path.name}.", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
        except (OSError, ValueError, TypeError, OverflowError, RecursionError) as exc:
            raise SaveError("Could not save campaign progress; the previous checkpoint was preserved.") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass  # Cleanup must not hide the original save failure.

    def preserve_existing(self) -> Path | None:
        """Copy existing bytes before an explicitly confirmed New Game.

        No parsing is involved: damaged and unsupported saves are recoverable
        too. Exclusive temporary creation gives each retained copy a unique
        name, and the original stays in place until a later save succeeds.
        """
        backup: Path | None = None
        try:
            try:
                source = self.path.open("rb")
            except FileNotFoundError:
                if self.exists():
                    raise SaveError("The existing checkpoint cannot be read for backup.")
                return None
            with source:
                with tempfile.NamedTemporaryFile(
                    mode="wb", dir=self.path.parent,
                    prefix=f"{self.path.name}.backup-", suffix=".json", delete=False,
                ) as destination:
                    backup = Path(destination.name)
                    shutil.copyfileobj(source, destination)
                    destination.flush()
                    os.fsync(destination.fileno())
            return backup
        except OSError as exc:
            if backup is not None:
                try:
                    backup.unlink(missing_ok=True)
                except OSError:
                    pass
            raise SaveError("Could not preserve the previous campaign; it was not replaced.") from exc
