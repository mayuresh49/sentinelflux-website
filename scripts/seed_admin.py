#!/usr/bin/env python3
"""Seed the first admin user into data/config.yaml.

Usage (from repo root, inside venv):
    python scripts/seed_admin.py --email admin@example.com --password yourpassword [--name "Your Name"]
"""
import argparse
import sys
from pathlib import Path

import bcrypt
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "data" / "config.yaml"


def main() -> None:
    p = argparse.ArgumentParser(description="Seed first admin user into data/config.yaml")
    p.add_argument("--email", required=True, help="Admin email address (used to log in)")
    p.add_argument("--password", required=True, help="Plain-text password (hashed before storage)")
    p.add_argument("--name", default="Admin", help="Display name (default: Admin)")
    args = p.parse_args()

    cfg: dict = {}
    if CONFIG_PATH.exists():
        cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}

    cfg.setdefault("users", [])

    if any(u.get("email", "").lower() == args.email.lower() for u in cfg["users"]):
        print(f"User {args.email} already exists — nothing changed.")
        sys.exit(0)

    pw_hash = bcrypt.hashpw(args.password.encode(), bcrypt.gensalt()).decode()
    cfg["users"].append({
        "email": args.email,
        "name": args.name,
        "admin": True,
        "password_hash": pw_hash,
        "products": [],
    })

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        yaml.dump(cfg, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Admin user '{args.name}' <{args.email}> created in {CONFIG_PATH}")


if __name__ == "__main__":
    main()
