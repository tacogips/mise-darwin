#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# ///
"""Local Runway Developer API CLI. No MCP or third-party runtime dependencies."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

API = "https://api.dev.runwayml.com/v1"
VERSION = "2024-11-06"
ENDPOINTS = (
    "text_to_image", "image_to_video", "text_to_video", "video_to_video",
    "text_to_speech", "text_to_music", "sound_effect", "video_to_audio",
)


class CliError(Exception):
    """An actionable error safe to display without credentials."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: object, code: int, msg: str,
                         headers: object, newurl: str) -> None:
        raise CliError("API redirect refused; credentials were not forwarded")


def task_path(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", identifier):
        raise CliError("Invalid task ID")
    return f"/tasks/{identifier}"


def read_payload(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise CliError("Input JSON must be an object")
    return cast(dict[str, object], value)


def request(method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    secret = os.environ.get("RUNWAYML_API_SECRET", "")
    if not secret:
        raise CliError("Set RUNWAYML_API_SECRET, or inject it with kinko exec")
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {secret}", "X-Runway-Version": VERSION,
        "Content-Type": "application/json", "Accept": "application/json",
    })
    try:
        with build_opener(NoRedirect()).open(req, timeout=60) as response:
            value: object = json.load(response)
    except HTTPError as error:
        # Server bodies can contain prompts or credentials; report only status.
        raise CliError(f"Runway API HTTP {error.code}; check credentials, credits, and request schema") from None
    except (URLError, TimeoutError):
        raise CliError("Runway API network request failed; no automatic generation retry") from None
    if not isinstance(value, dict):
        raise CliError("Runway returned an unexpected response")
    return cast(dict[str, object], value)


def wait_for_task(identifier: str, timeout: float, interval: float) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while True:
        task = request("GET", task_path(identifier))
        status = task.get("status")
        if status == "SUCCEEDED":
            return task
        if status in {"FAILED", "CANCELED", "CANCELLED"}:
            raise CliError(f"Task ended with status {status}; use task get for details")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CliError("Task polling timed out; the remote task continues. Resume with task wait")
        time.sleep(min(interval, remaining))


def download(identifier: str, index: int, output: Path) -> None:
    task = request("GET", task_path(identifier))
    outputs = task.get("output")
    if task.get("status") != "SUCCEEDED" or not isinstance(outputs, list):
        raise CliError("Task has no successful downloadable output")
    values = cast(list[object], outputs)
    if index < 0 or index >= len(values) or not isinstance(values[index], str):
        raise CliError("Output index is unavailable")
    url = cast(str, values[index])
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise CliError("Output must be an HTTPS URL without credentials")
    # Open exclusively: never overwrite an existing export. No API token on CDN requests.
    try:
        with output.open("xb") as target:
            try:
                with build_opener(NoRedirect()).open(url, timeout=60) as response:
                    while chunk := response.read(1024 * 1024):
                        target.write(chunk)
            except BaseException:
                output.unlink(missing_ok=True)
                raise
    except (URLError, TimeoutError):
        raise CliError("Output download failed; partial file removed") from None


def positive(value: str) -> float:
    number = float(value)
    if not 0 < number < float("inf"):
        raise argparse.ArgumentTypeError("Must be a positive finite number")
    return number


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="check local key presence; no API call")
    commands.add_parser("organization", help="read developer credit balance and usage tier")
    create = commands.add_parser("create", help="start one billable generation; no automatic retry")
    create.add_argument("endpoint", choices=ENDPOINTS)
    create.add_argument("--input", required=True, type=Path, help="API request JSON file")
    task = commands.add_parser("task").add_subparsers(dest="action", required=True)
    for name in ("get", "wait"):
        command = task.add_parser(name)
        command.add_argument("id")
        if name == "wait":
            command.add_argument("--timeout", type=positive, default=600.0)
            command.add_argument("--interval", type=positive, default=5.0)
    export = commands.add_parser("download", help="download one successful output without overwriting")
    export.add_argument("id")
    export.add_argument("--index", type=int, default=0)
    export.add_argument("--output", required=True, type=Path)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps({"api": API, "api_version": VERSION,
                              "key_present": bool(os.environ.get("RUNWAYML_API_SECRET")),
                              "transport": "https", "mcp": False}))
            return 0
        if args.command == "organization":
            result = request("GET", "/organization")
        elif args.command == "create":
            result = request("POST", f"/{args.endpoint}", read_payload(args.input))
        elif args.command == "task":
            result = (wait_for_task(args.id, args.timeout, args.interval)
                      if args.action == "wait" else request("GET", task_path(args.id)))
        else:
            download(args.id, args.index, args.output)
            print(json.dumps({"saved": str(args.output)}))
            return 0
        print(json.dumps(result, indent=2))
        return 0
    except (CliError, OSError, ValueError) as error:
        # Never include a secret even if a local OS error happens to echo it.
        secret = os.environ.get("RUNWAYML_API_SECRET", "")
        message = str(error)
        if secret:
            message = message.replace(secret, "[redacted]")
        print(json.dumps({"error": message}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
