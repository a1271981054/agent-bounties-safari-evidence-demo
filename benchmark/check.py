#!/usr/bin/env python3
"""Deterministic checks for a macOS Safari evidence bundle."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/workspace")
EVIDENCE = ROOT / "evidence"
NOT_BEFORE = datetime(2026, 8, 12, 0, 0, tzinfo=timezone.utc)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_json(name: str):
    path = EVIDENCE / name
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"invalid {name}: {error}")


def parse_png(path: Path) -> tuple[int, int]:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail("safari-homepage.png is not a valid PNG")
    width, height = struct.unpack(">II", data[16:24])
    if width < 1280 or height < 720:
        fail("safari-homepage.png must be at least 1280x720")
    return width, height


def main() -> None:
    screenshot = EVIDENCE / "safari-homepage.png"
    width, height = parse_png(screenshot)
    metadata = load_json("metadata.json")
    accessibility = load_json("accessibility.json")
    console = load_json("console.json")
    readme = EVIDENCE / "README.md"
    if not readme.is_file() or len(readme.read_text(encoding="utf-8").strip()) < 120:
        fail("evidence/README.md must explain the test steps and observed result")

    required = {
        "live_url",
        "captured_at_utc",
        "safari_version",
        "macos_version",
        "viewport",
        "screenshot_sha256",
        "public_run_url",
    }
    if not isinstance(metadata, dict) or not required.issubset(metadata):
        fail(f"metadata.json must include: {', '.join(sorted(required))}")
    if metadata["live_url"] != "https://agentbounties.app/":
        fail("live_url must be the production Agent Bounties homepage")
    if not re.fullmatch(r"\d+(?:\.\d+){0,3}", str(metadata["safari_version"])):
        fail("safari_version must be numeric")
    if not re.fullmatch(r"\d+(?:\.\d+){1,3}", str(metadata["macos_version"])):
        fail("macos_version must be numeric")
    try:
        captured = datetime.fromisoformat(str(metadata["captured_at_utc"]).replace("Z", "+00:00"))
    except ValueError:
        fail("captured_at_utc must be ISO 8601")
    if captured.tzinfo is None or captured.astimezone(timezone.utc) < NOT_BEFORE:
        fail("capture predates the bounty benchmark")
    viewport = metadata["viewport"]
    if not isinstance(viewport, dict) or viewport.get("width") != width or viewport.get("height") != height:
        fail("viewport dimensions must match the PNG")
    actual_sha = hashlib.sha256(screenshot.read_bytes()).hexdigest()
    if str(metadata["screenshot_sha256"]).lower().removeprefix("0x") != actual_sha:
        fail("screenshot_sha256 does not match the PNG")
    if not re.fullmatch(r"https://[^\s]+", str(metadata["public_run_url"])):
        fail("public_run_url must be an HTTPS URL")

    access_text = json.dumps(accessibility, sort_keys=True).lower()
    for phrase in ("agent bounties", "bounty board", "post a bounty"):
        if phrase not in access_text:
            fail(f"accessibility.json does not contain {phrase!r}")
    if not isinstance(console, list):
        fail("console.json must be an array")
    for entry in console:
        if isinstance(entry, dict) and str(entry.get("level", "")).lower() in {"error", "uncaught"}:
            fail("console.json contains an uncaught/error entry")

    print(json.dumps({"result": "pass", "png": {"width": width, "height": height, "sha256": actual_sha}}, sort_keys=True))


if __name__ == "__main__":
    main()
