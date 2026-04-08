#!/usr/bin/env python3
"""
ASQ Config Manager — user configuration + preferences for all ASQ skills.

Identity config (user_config.yaml) is auto-detected on first use.
Preferences (preferences.yaml) are optional overrides for opinionated defaults
like templates, tone, naming conventions, and workflow behaviors.

Subcommands:
  setup               Auto-detect SFDC identity and create config
  show                Print current config as YAML
  set                 Update a single config key
  get                 Get a single config value
  detect-identity     Auto-detect SFDC user ID and manager from sf CLI
  preferences-show    Show all preferences with current values (defaults + overrides)
  preferences-set     Override a preference
  preferences-reset   Reset a preference to its default
  preferences-export  Export all current preferences (defaults + overrides) as YAML
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    _req = Path(__file__).with_name("requirements.txt")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", str(_req)])
    import yaml

CONFIG_DIR = Path.home() / "asq-local-cache"
CONFIG_FILE = CONFIG_DIR / "user_config.yaml"
PREFS_FILE = CONFIG_DIR / "preferences.yaml"

# ===================================================================
# Genie Room defaults — shared across the org
# ===================================================================
DEFAULT_GENIE_ROOMS = {
    "default": "01f0467310751d7f9fb77993b8e49975",
    "Growth Accelerator for PAYG": "01f0cae151f512bebb0a4cb3c4bd8312",
}

# ===================================================================
# Default Preferences — every opinionated behavior lives here
# ===================================================================
# Users override these via `asq_config.py preferences-set <key> <value>`
# which writes to ~/asq-local-cache/preferences.yaml.
# Skills read merged values via get_preference().

DEFAULT_PREFERENCES = {
    # --- User Language ---
    # Preferred language for Claude's responses and skill outputs.
    # Skills will respond in this language. Triggers work in any language.
    "user.language": "en-us",

    # --- Status Notes ---
    "status_notes.format": "YYYY-MM-DD: (Meeting Type) <content>",
    "status_notes.language": "en-us",
    "status_notes.order": "newest_first",
    "status_notes.session_numbering": True,
    "status_notes.discovery_is_numbered": False,
    "status_notes.internal_sync_label": "(Internal Sync)",

    # --- CAST ---
    "cast.auto_cc_manager": True,
    "cast.sections": "Context, Ask, Success, Timeline",
    # Always CC the person who opened the ASQ on the CAST
    "cast.cc_requestor": True,
    # Extra SFDC user IDs to always CC (comma-separated), besides manager and requestor
    "cast.extra_cc_ids": "",
    # Timeline format guidance for LLM — describes the bullet structure
    "cast.timeline_format": (
        "Unordered list: (1) '1 Discovery session', "
        "(2) support-type-specific best practices sessions "
        "(e.g. '1 SDP Best Practices session', '1 MLflow Evaluation session', "
        "'1 Genie Best Practices session'), "
        "(3) optional implementation/development sessions, "
        "(4) always end with 'Follow-up sessions as needed'"
    ),

    # --- Closing Notes ---
    # Template uses {SITUATION}, {TASK}, {ACTION}, {RESULT} placeholders.
    # Separator line between sections.
    "close_notes.format": "STAR",
    "close_notes.separator": "------------------------------------",
    "close_notes.partial_tag": "#partiallycomplete",
    "close_notes.template": (
        "{partial_tag}\n"
        "{sep}\n"
        "SITUATION\n"
        "{sep}\n"
        "{situation}\n"
        "{sep}\n"
        "TASK\n"
        "{sep}\n"
        "{task}\n"
        "{sep}\n"
        "ACTION\n"
        "{sep}\n"
        "{action}\n"
        "{sep}\n"
        "RESULT\n"
        "{sep}\n"
        "{result}"
    ),

    # --- Tone ---
    "tone.sfdc": "professional",
    "tone.slack": "friendly",
    "tone.sfdc_description": "Concise, factual, third-person where appropriate",
    "tone.slack_description": "Casual, uses bullet points, matches channel style",

    # --- Slack Channel Naming ---
    # Pattern uses: {number}, {account_slug}, {type_slug}
    "slack.channel_pattern": "ar-{number}-{account_slug}-{type_slug}",
    # Merged channel name when multiple ASQs share a requestor
    "slack.merged_channel_pattern": "sts-support-{account_slug}",
    # Intro message uses: {creator}, {support_type}, {account}, {slots}
    "slack.intro_template": (
        "Hey @{creator}, created this channel for the {support_type} ASQ for "
        "{account}. Could we set up a quick sync? Here are some times that work: {slots}"
    ),
    # Closing message uses: {account}, {support_type}, {summary}
    "slack.closing_template": (
        "Wrapping up the {support_type} engagement for {account}. {summary} "
        "Thanks for the collaboration! Feel free to reach out if anything else comes up."
    ),
    "slack.detect_language": True,

    # --- Support Type Slugs (for channel names) ---
    "slugs.ML & GenAI": "ml-genai",
    "slugs.Data Engineering": "data-eng",
    "slugs.Data Warehousing": "data-wh",
    "slugs.Platform Administration": "platform-admin",
    "slugs.Streaming": "streaming",
    "slugs.Data Governance": "data-gov",
    "slugs.Launch Accelerator": "launch-accel",
    "slugs.Growth Accelerator for PAYG": "growth-accel",

    # --- Custom Triggers ---
    # Users can store their own trigger phrases here for reference.
    # These are NOT automatically used for routing — to activate them,
    # ask Claude to add custom trigger mappings to your ~/.claude/CLAUDE.md.
    "triggers.asq-update": "",
    "triggers.asq-close": "",
    "triggers.asq-onboarding": "",
    "triggers.asq-refresher": "",

    # --- Obsidian Layout ---
    "obsidian.active_path": "ASQ/Active",
    "obsidian.archive_path": "ASQ/Archive",
    "obsidian.accounts_path": "Accounts",
}

# Human-readable descriptions for each preference (for preferences-show)
PREFERENCE_DESCRIPTIONS = {
    "user.language": "Preferred language for Claude responses (en-us, pt-br, es, etc.)",
    "status_notes.format": "Date/label format for SFDC status note entries",
    "status_notes.language": "Language for status notes (en-us, pt-br, etc.)",
    "status_notes.order": "Note ordering: newest_first or oldest_first",
    "status_notes.session_numbering": "Number customer sessions (1st Meeting, 2nd Meeting)",
    "status_notes.discovery_is_numbered": "Whether discovery counts as a numbered session",
    "status_notes.internal_sync_label": "Label for internal sync meetings",
    "cast.auto_cc_manager": "Auto-CC your manager on every CAST",
    "cast.cc_requestor": "Auto-CC the ASQ requestor (person who opened it) on every CAST",
    "cast.sections": "CAST section names (comma-separated)",
    "cast.extra_cc_ids": "Extra SFDC user IDs to always CC (comma-separated)",
    "cast.timeline_format": "LLM guidance for Timeline bullet structure",
    "close_notes.format": "Close notes format name (STAR, custom, etc.)",
    "close_notes.separator": "Line separator between sections",
    "close_notes.partial_tag": "Tag for partially complete closures",
    "close_notes.template": "Full close notes template with placeholders",
    "tone.sfdc": "Tone for SFDC updates (professional, neutral, etc.)",
    "tone.slack": "Tone for Slack messages (friendly, professional, etc.)",
    "tone.sfdc_description": "Description of SFDC tone for LLM guidance",
    "tone.slack_description": "Description of Slack tone for LLM guidance",
    "slack.channel_pattern": "Slack channel naming pattern",
    "slack.merged_channel_pattern": "Channel name when merging multiple ASQs",
    "slack.intro_template": "Intro message template for new channels",
    "slack.closing_template": "Closing message template",
    "slack.detect_language": "Auto-detect Slack channel language",
    "triggers.asq-update": "Custom trigger phrases for asq-update (comma-separated, any language)",
    "triggers.asq-close": "Custom trigger phrases for asq-close (comma-separated, any language)",
    "triggers.asq-onboarding": "Custom trigger phrases for asq-onboarding (comma-separated, any language)",
    "triggers.asq-refresher": "Custom trigger phrases for asq-refresher (comma-separated, any language)",
    "obsidian.active_path": "Obsidian path for active ASQ pages",
    "obsidian.archive_path": "Obsidian path for archived ASQ pages",
    "obsidian.accounts_path": "Obsidian path for account pages",
}

# ===================================================================
# Config helpers
# ===================================================================

DEFAULT_CONFIG = {
    "sfdc_user_id": None,
    "sfdc_username": None,
    "user_name": None,
    "manager_sfdc_id": None,
    "manager_name": None,
    "obsidian_vault_path": None,
    "genie_rooms": dict(DEFAULT_GENIE_ROOMS),
    "created_at": None,
    "last_updated": None,
}


def _run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None


def load_config():
    if not CONFIG_FILE.exists():
        return None
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f) or {}


def save_config(config):
    CONFIG_DIR.mkdir(exist_ok=True)
    config["last_updated"] = str(date.today())
    if not config.get("created_at"):
        config["created_at"] = config["last_updated"]
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def require_config():
    config = load_config()
    if not config or not config.get("sfdc_user_id"):
        print(json.dumps({
            "error": "CONFIG_NOT_FOUND",
            "message": "User config not set up yet. Run: python3 asq_config.py setup",
            "setup_instructions": (
                "Run `asq_config.py detect-identity` to auto-detect identity, "
                "then `asq_config.py setup --user-id <id> --user-name <name> "
                "--manager-id <id> --manager-name <name>`."
            ),
        }))
        sys.exit(1)
    return config


# ===================================================================
# Preferences helpers
# ===================================================================

def load_preferences():
    """Load user preference overrides from preferences.yaml."""
    if not PREFS_FILE.exists():
        return {}
    with open(PREFS_FILE) as f:
        return yaml.safe_load(f) or {}


def save_preferences(prefs):
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(PREFS_FILE, "w") as f:
        yaml.dump(prefs, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_preference(key):
    """Get a preference value: user override if set, else default."""
    overrides = load_preferences()
    if key in overrides:
        return overrides[key]
    return DEFAULT_PREFERENCES.get(key)


def get_all_preferences():
    """Return merged dict of all preferences (defaults + overrides)."""
    merged = dict(DEFAULT_PREFERENCES)
    merged.update(load_preferences())
    return merged


def get_slug(support_type):
    """Get the channel slug for a support type."""
    slug = get_preference(f"slugs.{support_type}")
    if slug:
        return slug
    # Fallback: slugify the support type
    return support_type.lower().replace(" & ", "-").replace(" ", "-")


# ===================================================================
# Subcommands: identity
# ===================================================================

def cmd_detect_identity(args):
    result = {"detected": {}, "errors": []}

    raw = _run(["sf", "org", "display", "--json"])
    if not raw:
        result["errors"].append("sf CLI not authenticated. Run `sf org login web` first.")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    try:
        org_data = json.loads(raw)
        username = org_data.get("result", {}).get("username")
        if not username:
            result["errors"].append("Could not determine username from sf org display.")
            print(json.dumps(result, indent=2))
            sys.exit(1)
        result["detected"]["sfdc_username"] = username
    except json.JSONDecodeError:
        result["errors"].append("Failed to parse sf org display output.")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    import urllib.parse
    soql = (
        f"SELECT Id, Name, ManagerId, Manager.Name, Manager.Email "
        f"FROM User WHERE Username = '{username}'"
    )
    encoded = urllib.parse.quote(soql)
    raw = _run(
        ["sf", "api", "request", "rest",
         f"/services/data/v66.0/query?q={encoded}",
         "--method", "GET"],
        timeout=30,
    )
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                data = data[0] if data else {}
            records = data.get("records", [])
            if records:
                user = records[0]
                result["detected"]["sfdc_user_id"] = user.get("Id")
                result["detected"]["user_name"] = user.get("Name")
                manager = user.get("Manager") or {}
                if isinstance(manager, dict):
                    manager.pop("attributes", None)
                    result["detected"]["manager_sfdc_id"] = user.get("ManagerId")
                    result["detected"]["manager_name"] = manager.get("Name")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            result["errors"].append(f"Failed to parse user query result: {e}")
    else:
        result["errors"].append("SFDC user query returned no results.")

    print(json.dumps(result, indent=2))


def cmd_setup(args):
    config = load_config() or dict(DEFAULT_CONFIG)

    if args.user_id:
        config["sfdc_user_id"] = args.user_id
    if args.username:
        config["sfdc_username"] = args.username
    if args.user_name:
        config["user_name"] = args.user_name
    if args.manager_id:
        config["manager_sfdc_id"] = args.manager_id
    if args.manager_name:
        config["manager_name"] = args.manager_name
    if args.obsidian_vault:
        config["obsidian_vault_path"] = args.obsidian_vault

    if "genie_rooms" not in config or not config["genie_rooms"]:
        config["genie_rooms"] = dict(DEFAULT_GENIE_ROOMS)

    save_config(config)
    print(f"Config saved to {CONFIG_FILE}")
    print(yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False))


# ===================================================================
# Subcommands: config read/write
# ===================================================================

def cmd_show(args):
    config = load_config()
    if not config:
        print("No config found. Run setup first.")
        sys.exit(1)
    print(yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False))


def cmd_get(args):
    config = require_config()
    keys = args.key.split(".")
    val = config
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            val = None
            break
    if val is None:
        print(f"NOT_SET: {args.key}")
        sys.exit(1)
    print(val)


def cmd_set(args):
    config = load_config() or dict(DEFAULT_CONFIG)
    keys = args.key.split(".")
    target = config
    for k in keys[:-1]:
        if k not in target or not isinstance(target[k], dict):
            target[k] = {}
        target = target[k]
    target[keys[-1]] = args.value
    save_config(config)
    print(f"Set {args.key} = {args.value}")


# ===================================================================
# Subcommands: preferences
# ===================================================================

def cmd_preferences_show(args):
    """Show all preferences with defaults and any user overrides."""
    overrides = load_preferences()
    category = args.category

    output = []
    for key in sorted(DEFAULT_PREFERENCES.keys()):
        if category and not key.startswith(category + "."):
            continue
        default = DEFAULT_PREFERENCES[key]
        current = overrides.get(key, default)
        is_overridden = key in overrides
        desc = PREFERENCE_DESCRIPTIONS.get(key, "")

        entry = {
            "key": key,
            "value": current,
            "default": default,
            "overridden": is_overridden,
        }
        if desc:
            entry["description"] = desc
        output.append(entry)

    # Check for extra user-defined keys not in defaults
    for key, val in sorted(overrides.items()):
        if key not in DEFAULT_PREFERENCES:
            if category and not key.startswith(category + "."):
                continue
            output.append({
                "key": key,
                "value": val,
                "default": None,
                "overridden": True,
                "description": "(custom user preference)",
            })

    print(json.dumps(output, indent=2, default=str, ensure_ascii=False))


def cmd_preferences_set(args):
    """Set a preference override."""
    prefs = load_preferences()

    # Coerce booleans and numbers
    val = args.value
    if val.lower() in ("true", "yes"):
        val = True
    elif val.lower() in ("false", "no"):
        val = False
    else:
        try:
            val = int(val)
        except ValueError:
            pass

    prefs[args.key] = val
    save_preferences(prefs)

    default = DEFAULT_PREFERENCES.get(args.key, "(no default)")
    print(f"Set {args.key} = {val}")
    if args.key in DEFAULT_PREFERENCES:
        print(f"Default was: {default}")


def cmd_preferences_reset(args):
    """Reset a preference to its default."""
    prefs = load_preferences()
    if args.key in prefs:
        del prefs[args.key]
        save_preferences(prefs)
        default = DEFAULT_PREFERENCES.get(args.key, "(no default)")
        print(f"Reset {args.key} to default: {default}")
    else:
        print(f"{args.key} was already at default")


def cmd_preferences_export(args):
    """Export all current preferences (defaults + overrides) as YAML."""
    merged = get_all_preferences()
    # Group by category for readability
    grouped = {}
    for key, val in sorted(merged.items()):
        cat = key.split(".")[0]
        if cat not in grouped:
            grouped[cat] = {}
        grouped[cat][key] = val

    print(yaml.dump(grouped, default_flow_style=False, allow_unicode=True, sort_keys=False))


# ===================================================================
# CLI
# ===================================================================

def main():
    parser = argparse.ArgumentParser(description="ASQ Config & Preferences Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- Identity ---
    p = sub.add_parser("detect-identity", help="Auto-detect SFDC user ID and manager")
    p.set_defaults(func=cmd_detect_identity)

    p = sub.add_parser("setup", help="Create or update user config")
    p.add_argument("--user-id", help="SFDC User ID")
    p.add_argument("--username", help="SFDC Username (email)")
    p.add_argument("--user-name", help="Display name")
    p.add_argument("--manager-id", help="Manager's SFDC User ID")
    p.add_argument("--manager-name", help="Manager's display name")
    p.add_argument("--obsidian-vault", help="Path to Obsidian vault")
    p.set_defaults(func=cmd_setup)

    # --- Config ---
    p = sub.add_parser("show", help="Print current config")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("get", help="Get a config value")
    p.add_argument("key", help="Config key (dot-separated)")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("set", help="Set a config value")
    p.add_argument("key", help="Config key (dot-separated)")
    p.add_argument("value", help="Value to set")
    p.set_defaults(func=cmd_set)

    # --- Preferences ---
    p = sub.add_parser("preferences-show", help="Show all preferences")
    p.add_argument("category", nargs="?",
                   help="Filter by category (status_notes, cast, close_notes, tone, slack, slugs, obsidian)")
    p.set_defaults(func=cmd_preferences_show)

    p = sub.add_parser("preferences-set", help="Override a preference")
    p.add_argument("key", help="Preference key (e.g. tone.slack)")
    p.add_argument("value", help="New value")
    p.set_defaults(func=cmd_preferences_set)

    p = sub.add_parser("preferences-reset", help="Reset a preference to default")
    p.add_argument("key", help="Preference key to reset")
    p.set_defaults(func=cmd_preferences_reset)

    p = sub.add_parser("preferences-export", help="Export all preferences as YAML")
    p.set_defaults(func=cmd_preferences_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
