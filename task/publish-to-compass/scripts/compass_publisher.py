#!/usr/bin/env python3
"""Compass fact publisher - publishes fact payload JSON files to Compass SoundCheck.

Reads fact files from a directory, validates them, and POSTs each to the Compass
Facts API. Supports dry-run mode.

Usage:
    COMPASS_API_KEY="..." COMPASS_URL="https://..." DRY_RUN=false \\
        python -m publish_to_compass.scripts.compass_publisher --facts-dir /mnt/facts

Environment:
    COMPASS_API_KEY  - Bearer token for the Compass Facts API.
    COMPASS_URL      - Compass Facts API endpoint URL.
    DRY_RUN          - Set to "false" to actually publish (default: dry-run).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

from .compass_fact_validator import validate_compass_fact_file


def publish_facts(
    facts_dir: Path,
    compass_url: str,
    api_key: str,
    dry_run: bool,
) -> int:
    """Publish fact files to Compass.

    Args:
        facts_dir: Directory containing fact JSON files
        compass_url: Compass Facts API endpoint URL
        api_key: Compass API key (Bearer token)
        dry_run: If True, validate and report but don't POST

    Returns:
        Exit code (0 = success, 1 = one or more failures)
    """
    if not compass_url or not api_key:
        print(
            "ERROR: compass-url and api-key must have non-empty values",
            file=sys.stderr,
        )
        return 1

    files = sorted(facts_dir.glob("*.json"))
    if not files:
        print("ERROR: No fact files found", file=sys.stderr)
        return 1

    # Use mounted internal CA if present, otherwise system default
    ca_bundle = "/tmp/ca/ca.crt" if Path("/tmp/ca/ca.crt").exists() else True

    mode = "DRY RUN" if dry_run else "LIVE"
    failed = 0
    print(f"=== Compass publish ({mode}): {len(files)} fact(s) ===")

    for f in files:
        try:
            file_data = validate_compass_fact_file(f)
        except Exception as e:
            print(f"SKIP {f.name}: schema validation failed: {e}")
            failed += 1
            continue

        fact_refs = ", ".join(fact["factRef"] for fact in file_data["facts"])
        data = json.dumps(file_data)

        if dry_run:
            print(f"[DRY RUN] Would POST {fact_refs} ({len(data)} bytes)")
            continue

        try:
            resp = httpx.post(
                compass_url,
                content=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=30.0,
                verify=ca_bundle,
            )
            if resp.status_code >= 200 and resp.status_code < 300:
                print(f"OK   {fact_refs} (HTTP {resp.status_code})")
            else:
                print(
                    f"FAIL {fact_refs} (HTTP {resp.status_code}: {resp.reason_phrase})"
                )
                failed += 1
        except httpx.HTTPError as e:
            print(f"FAIL {fact_refs} ({e})")
            failed += 1

    total = len(files)
    if dry_run:
        print(f"Dry run complete: {total} fact(s) would be published")
    else:
        print(f"Published {total - failed}/{total} facts")
    return 1 if failed else 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Publish fact files to Compass SoundCheck")
    parser.add_argument(
        "--facts-dir",
        type=Path,
        required=True,
        help="Directory containing fact payload JSON files",
    )
    args = parser.parse_args()

    compass_url = os.environ.get("COMPASS_URL", "")
    api_key = os.environ.get("COMPASS_API_KEY", "")
    dry_run = os.environ.get("DRY_RUN", "true").lower() != "false"
    return publish_facts(
        args.facts_dir,
        compass_url,
        api_key,
        dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
