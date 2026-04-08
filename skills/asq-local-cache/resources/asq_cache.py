#!/usr/bin/env python3
"""ASQ Local Cache Manager — stores stable ASQ metadata as YAML files."""

import argparse
import sys
from pathlib import Path
from datetime import date

try:
    import yaml
except ImportError:
    import subprocess
    print("Installing PyYAML...", file=sys.stderr)
    _req = Path(__file__).with_name("requirements.txt")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", str(_req)])
    import yaml

CACHE_DIR = Path.home() / "asq-local-cache"
INDEX_FILE = CACHE_DIR / "index.yaml"


def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            return yaml.safe_load(f) or {}
    return {}


def save_index(index):
    CACHE_DIR.mkdir(exist_ok=True)
    with open(INDEX_FILE, "w") as f:
        yaml.dump(index, f, default_flow_style=False, allow_unicode=True)


def load_record(ar_number):
    path = CACHE_DIR / f"{ar_number}.yaml"
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return None


def save_record(ar_number, record):
    CACHE_DIR.mkdir(exist_ok=True)
    record["last_updated"] = str(date.today())
    path = CACHE_DIR / f"{ar_number}.yaml"
    with open(path, "w") as f:
        yaml.dump(record, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    _update_index_for(ar_number, record)


def _update_index_for(ar_number, record):
    index = load_index()
    keys = [ar_number.lower(), record.get("account_name", "").lower()]
    keys += [a.lower() for a in record.get("known_aliases", [])]
    for key in keys:
        if key:
            index[key] = ar_number
    save_index(index)


def rebuild_index():
    index = {}
    for f in CACHE_DIR.glob("AR-*.yaml"):
        record = yaml.safe_load(f.read_text()) or {}
        ar = record.get("ar_number", f.stem)
        keys = [ar.lower(), record.get("account_name", "").lower()]
        keys += [a.lower() for a in record.get("known_aliases", [])]
        for key in keys:
            if key:
                index[key] = ar
    save_index(index)
    print(f"Rebuilt index with {len(index)} entries")


def lookup(query):
    query_lower = query.lower().strip()
    index = load_index()

    # Exact match
    if query_lower in index:
        record = load_record(index[query_lower])
        if record:
            print(yaml.dump(record, default_flow_style=False, allow_unicode=True, sort_keys=False))
            return

    # Fuzzy: substring match on index keys
    matches = []
    for key, ar in index.items():
        if query_lower in key or key in query_lower:
            if ar not in matches:
                matches.append(ar)

    if len(matches) == 1:
        record = load_record(matches[0])
        if record:
            print(yaml.dump(record, default_flow_style=False, allow_unicode=True, sort_keys=False))
            return
    elif len(matches) > 1:
        print(f"Multiple matches found:")
        for ar in matches:
            rec = load_record(ar)
            print(f"  {ar}: {rec.get('account_name', '?')}")
        return

    # Fuzzy: scan all files for partial match in account_name or aliases
    for f in CACHE_DIR.glob("AR-*.yaml"):
        record = yaml.safe_load(f.read_text()) or {}
        searchable = [record.get("account_name", "").lower()]
        searchable += [a.lower() for a in record.get("known_aliases", [])]
        for s in searchable:
            if query_lower in s or s in query_lower:
                print(yaml.dump(record, default_flow_style=False, allow_unicode=True, sort_keys=False))
                return

    print(f"NOT_FOUND: No cached ASQ matches '{query}'")
    sys.exit(1)


def upsert(ar_number, fields):
    record = load_record(ar_number) or {"ar_number": ar_number}

    for key, value in fields.items():
        if key in ("known_aliases", "known_email_threads"):
            existing = record.get(key, [])
            if value not in existing:
                existing.append(value)
            record[key] = existing
        elif key == "known_calendar_events":
            # Expects "event_id:summary:recurrence" format
            parts = value.split(":", 2)
            event = {"event_id": parts[0]}
            if len(parts) > 1:
                event["summary"] = parts[1]
            if len(parts) > 2:
                event["recurrence"] = parts[2]
            existing = record.get(key, [])
            if not any(e.get("event_id") == event["event_id"] for e in existing):
                existing.append(event)
            record[key] = existing
        else:
            record[key] = value

    save_record(ar_number, record)
    print(f"Updated {ar_number}")


def add_alias(ar_number, alias):
    record = load_record(ar_number)
    if not record:
        print(f"ERROR: {ar_number} not found in cache")
        sys.exit(1)
    aliases = record.get("known_aliases", [])
    if alias not in aliases:
        aliases.append(alias)
        record["known_aliases"] = aliases
        save_record(ar_number, record)
        print(f"Added alias '{alias}' to {ar_number}")
    else:
        print(f"Alias '{alias}' already exists for {ar_number}")


def list_all():
    files = sorted(CACHE_DIR.glob("AR-*.yaml"))
    if not files:
        print("No cached ASQs found.")
        return
    for f in files:
        record = yaml.safe_load(f.read_text()) or {}
        ar = record.get("ar_number", f.stem)
        account = record.get("account_name", "?")
        aliases = ", ".join(record.get("known_aliases", []))
        status = record.get("support_type", "")
        print(f"  {ar}: {account} ({status}){f' — aliases: {aliases}' if aliases else ''}")


def main():
    parser = argparse.ArgumentParser(description="ASQ Local Cache Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_lookup = sub.add_parser("lookup", help="Find ASQ by AR number, account name, or alias")
    p_lookup.add_argument("query", help="Search query")

    p_upsert = sub.add_parser("upsert", help="Create or update a cache entry")
    p_upsert.add_argument("--ar", required=True, help="AR number (e.g. AR-000107402)")
    p_upsert.add_argument("--field", action="append", required=True, help="key=value pair")

    p_alias = sub.add_parser("add-alias", help="Add an alias to an existing entry")
    p_alias.add_argument("--ar", required=True, help="AR number")
    p_alias.add_argument("--alias", required=True, help="Alias to add")

    sub.add_parser("list", help="List all cached ASQs")
    sub.add_parser("rebuild-index", help="Rebuild the index from YAML files")

    args = parser.parse_args()

    if args.command == "lookup":
        lookup(args.query)
    elif args.command == "upsert":
        fields = {}
        for f in args.field:
            k, v = f.split("=", 1)
            fields[k] = v
        upsert(args.ar, fields)
    elif args.command == "add-alias":
        add_alias(args.ar, args.alias)
    elif args.command == "list":
        list_all()
    elif args.command == "rebuild-index":
        rebuild_index()


if __name__ == "__main__":
    main()
