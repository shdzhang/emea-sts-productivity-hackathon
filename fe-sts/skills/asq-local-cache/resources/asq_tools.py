#!/usr/bin/env python3
"""
ASQ Tools — unified CLI for all ASQ skill operations.

All user-specific values (SFDC user ID, manager, vault path, Genie rooms) are
loaded from ~/asq-local-cache/user_config.yaml.  Run `asq_config.py setup` to
create it on first use.

Subcommands:
  gather            Read-only context gathering (cache + SFDC + calendar + gmail + obsidian)
  sfdc-query        Run a SOQL query and return JSON records
  sfdc-update       PATCH an SFDC record from a JSON file
  sfdc-batch-update Batch PATCH multiple SFDC records from a single JSON file
  sfdc-chatter      Post a raw Chatter payload from a JSON file (low-level)
  cast-post         Build and post a CAST from plain text args (high-level, always clean formatting)
  sfdc-chatter-read Read Chatter feed elements from an SFDC record
  list-active       List all active ASQs for weekly review
  close             Prepare and validate ASQ closing payload
  discover-new      Find ASQs with no status notes (for onboarding)
  obsidian-read     Read an ASQ page from Obsidian vault
  obsidian-patch    Append content under a heading in an Obsidian ASQ file
  availability      Find calendar availability for the next N days
  sts-index         Print the STS content index (support type -> searchable titles)
"""

import argparse
import json
import subprocess
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    _req = Path(__file__).with_name("requirements.txt")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", str(_req)])
    import yaml

# ---------------------------------------------------------------------------
# Paths & Config
# ---------------------------------------------------------------------------
CACHE_SCRIPT = Path(__file__).parent / "asq_cache.py"
CONFIG_SCRIPT = Path(__file__).parent / "asq_config.py"
OBSIDIAN_PREF = Path.home() / "asq-local-cache" / "obsidian_preference.yaml"


def _load_user_config():
    """Load user config, exiting with setup instructions if missing."""
    config_file = Path.home() / "asq-local-cache" / "user_config.yaml"
    if not config_file.exists():
        print(json.dumps({
            "error": "CONFIG_NOT_FOUND",
            "message": (
                "First-time setup required. Run the following to auto-detect your identity:\n"
                f"  python3 {CONFIG_SCRIPT} detect-identity\n"
                "Then confirm the values and run:\n"
                f"  python3 {CONFIG_SCRIPT} setup --user-id <id> --user-name <name> "
                "--manager-id <id> --manager-name <name>"
            ),
        }))
        sys.exit(1)
    with open(config_file) as f:
        return yaml.safe_load(f) or {}


def _get_config_value(config, key, required=True):
    """Get a value from config, erroring if required and missing."""
    val = config.get(key)
    if required and not val:
        print(json.dumps({
            "error": f"CONFIG_MISSING_{key.upper()}",
            "message": f"Config key '{key}' is not set. Run: python3 {CONFIG_SCRIPT} set {key} <value>",
        }))
        sys.exit(1)
    return val


# Load config and preferences at module level
_CONFIG = None
_PREFS_MODULE = None


def _config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _load_user_config()
    return _CONFIG


def _prefs():
    """Lazy-load the asq_config module for preference access."""
    global _PREFS_MODULE
    if _PREFS_MODULE is None:
        sys.path.insert(0, str(Path(__file__).parent))
        import asq_config
        _PREFS_MODULE = asq_config
    return _PREFS_MODULE


def _get_pref(key):
    """Get a preference value (user override or default)."""
    return _prefs().get_preference(key)


def _get_all_prefs():
    """Get all preferences merged (defaults + overrides)."""
    return _prefs().get_all_preferences()


def _sfdc_user_id():
    return _get_config_value(_config(), "sfdc_user_id")


def _manager_sfdc_id():
    return _get_config_value(_config(), "manager_sfdc_id")


def _obsidian_vault_path():
    """Return configured Obsidian vault path, or None."""
    path = _config().get("obsidian_vault_path")
    if path:
        return Path(path).expanduser()
    return None


def _genie_rooms():
    """Return Genie room mapping from config, with defaults."""
    rooms = _config().get("genie_rooms")
    if not rooms:
        return _prefs().DEFAULT_GENIE_ROOMS.copy()
    return rooms


def _find_google_script(skill_name, script_name):
    matches = sorted(Path.home().glob(
        f".claude/plugins/cache/fe-vibe/fe-google-tools/*/skills/{skill_name}/resources/{script_name}"
    ))
    return matches[-1] if matches else None


GMAIL_SCRIPT = _find_google_script("gmail", "gmail_builder.py")
GCAL_SCRIPT = _find_google_script("google-calendar", "gcal_builder.py")

# ---------------------------------------------------------------------------
# STS Content Index — searchable titles instead of local file paths
# ---------------------------------------------------------------------------
# Maps support types to page titles / search queries that can be used with
# Glean, Confluence, or Obsidian MCP to fetch fresh content on demand.
# This avoids stale local copies and keeps the source of truth authoritative.

STS_CONTENT_INDEX = {
    "Platform Administration": {
        "pages": ["STS Workspace Setup", "STS Delivery and Resources", "STS Workspace Setup FAQ"],
        "search_query": "STS Content Repo Workspace Setup",
        "keywords": ["workspace", "platform", "CI/CD", "observability", "serverless"],
    },
    "Data Governance": {
        "pages": ["STS Data Governance", "STS UC FAQ", "STS UC Learning Sessions"],
        "search_query": "STS Content Repo Data Governance Unity Catalog",
        "keywords": ["unity catalog", "data governance", "UC"],
    },
    "Data Engineering": {
        "pages": ["STS Data Engineering"],
        "search_query": "STS Content Repo Data Engineering",
        "keywords": ["ETL", "lakeflow", "orchestration", "delta", "data sharing", "streaming"],
    },
    "Data Warehousing": {
        "pages": ["STS Data Warehousing", "STS Courses Recommendation"],
        "search_query": "STS Content Repo Data Warehousing",
        "keywords": ["DBSQL", "SQL analytics", "AI/BI", "genie", "dashboard", "lakebridge"],
    },
    "ML & GenAI": {
        "pages": ["STS ML & GenAI"],
        "search_query": "STS Content Repo ML GenAI",
        "keywords": ["MLOps", "LLMOps", "MLflow", "RAG", "AI agents", "model serving"],
    },
    "Launch Accelerator": {
        "pages": ["STS Launch Accelerator", "STS LA Execution Guide", "STS LA FAQ", "STS LA Red Flags"],
        "search_query": "STS Content Repo Launch Accelerator",
        "keywords": ["launch accelerator", "LA", "PAYG", "growth accelerator"],
    },
    "Streaming": {
        "pages": ["STS Data Engineering"],
        "search_query": "STS Content Repo Streaming Data Engineering",
        "keywords": ["streaming", "structured streaming", "kafka"],
    },
}

# Cross-cutting resources available for all support types
STS_CROSS_CUTTING = {
    "pages": ["STS Email Templates", "STS Service Expertise Definitions", "STS Overview (go-sts)"],
    "search_query": "STS Content Repo overview service expertise",
}


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=isinstance(cmd, str),
        )
        stdout = r.stdout.strip()
        if r.returncode != 0:
            detail = r.stderr.strip() or stdout or "unknown error"
            return f"ERROR (exit {r.returncode}): {detail[:500]}"
        if stdout:
            try:
                parsed = json.loads(stdout)
                if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and "errorCode" in parsed[0]:
                    return f"ERROR (SFDC): {parsed[0].get('errorCode')}: {parsed[0].get('message', '')}"
                if isinstance(parsed, dict) and "errorCode" in parsed:
                    return f"ERROR (SFDC): {parsed.get('errorCode')}: {parsed.get('message', '')}"
            except (json.JSONDecodeError, TypeError):
                pass
        return stdout
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out"
    except Exception as e:
        return f"ERROR: {e}"


def truncate(text, max_chars=4000, keep_start=500):
    if not text or len(text) <= max_chars:
        return text
    return text[:keep_start] + "\n...(truncated)...\n" + text[-(max_chars - keep_start):]


def _obsidian_enabled():
    try:
        with open(OBSIDIAN_PREF) as f:
            return yaml.safe_load(f).get("obsidian_enabled", False)
    except Exception:
        return False

# ---------------------------------------------------------------------------
# SFDC primitives
# ---------------------------------------------------------------------------

def sfdc_query(soql, timeout=30):
    """Run SOQL, return list of record dicts."""
    encoded = urllib.parse.quote(soql)
    raw = run_cmd(
        ["sf", "api", "request", "rest",
         f"/services/data/v66.0/query?q={encoded}",
         "--method", "GET"],
        timeout=timeout,
    )
    if raw.startswith("ERROR"):
        raise RuntimeError(raw)
    data = json.loads(raw)
    if isinstance(data, list):
        data = data[0] if data else {}
    records = data.get("records", []) if isinstance(data, dict) else []
    for r in records:
        r.pop("attributes", None)
        for key, val in list(r.items()):
            if isinstance(val, dict):
                val.pop("attributes", None)
    return records


def sfdc_update(object_id, json_path):
    """PATCH an SFDC record. json_path is a file containing the update payload."""
    return run_cmd(
        ["sf", "api", "request", "rest",
         "--method", "PATCH",
         f"/services/data/v66.0/sobjects/ApprovalRequest__c/{object_id}",
         "--body", f"@{json_path}"],
        timeout=30,
    )


def sfdc_chatter(json_path):
    """POST a Chatter feed element from a raw JSON file."""
    return run_cmd(
        ["sf", "api", "request", "rest",
         "--method", "POST",
         "/services/data/v66.0/chatter/feed-elements",
         "--body", f"@{json_path}"],
        timeout=30,
    )


def build_cast_payload(record_id, context, ask, success, timeline_lines, cc_ids):
    """Build a properly-formatted CAST Chatter payload from plain text inputs."""
    segments = []

    def _add_section(header, body_text):
        segments.append({"type": "MarkupBegin", "markupType": "Paragraph"})
        segments.append({"type": "MarkupBegin", "markupType": "Bold"})
        segments.append({"type": "Text", "text": f"{header}:"})
        segments.append({"type": "MarkupEnd", "markupType": "Bold"})
        segments.append({"type": "MarkupEnd", "markupType": "Paragraph"})
        segments.append({"type": "MarkupBegin", "markupType": "Paragraph"})
        segments.append({"type": "Text", "text": body_text})
        segments.append({"type": "MarkupEnd", "markupType": "Paragraph"})
        segments.append({"type": "MarkupBegin", "markupType": "Paragraph"})
        segments.append({"type": "Text", "text": "\u00a0"})
        segments.append({"type": "MarkupEnd", "markupType": "Paragraph"})

    _add_section("Context", context)
    _add_section("Ask", ask)
    _add_section("Success", success)

    # Timeline
    segments.append({"type": "MarkupBegin", "markupType": "Paragraph"})
    segments.append({"type": "MarkupBegin", "markupType": "Bold"})
    segments.append({"type": "Text", "text": "Timeline:"})
    segments.append({"type": "MarkupEnd", "markupType": "Bold"})
    segments.append({"type": "MarkupEnd", "markupType": "Paragraph"})
    for line in timeline_lines:
        bullet = line if line.startswith("- ") else f"- {line}"
        segments.append({"type": "MarkupBegin", "markupType": "Paragraph"})
        segments.append({"type": "Text", "text": bullet})
        segments.append({"type": "MarkupEnd", "markupType": "Paragraph"})
    segments.append({"type": "MarkupBegin", "markupType": "Paragraph"})
    segments.append({"type": "Text", "text": "\u00a0"})
    segments.append({"type": "MarkupEnd", "markupType": "Paragraph"})

    # C/C section
    segments.append({"type": "MarkupBegin", "markupType": "Paragraph"})
    segments.append({"type": "Text", "text": "C/C: "})
    for i, uid in enumerate(cc_ids):
        if i > 0:
            segments.append({"type": "Text", "text": ", "})
        segments.append({"type": "Mention", "id": uid})
    segments.append({"type": "MarkupEnd", "markupType": "Paragraph"})

    return {
        "body": {"messageSegments": segments},
        "feedElementType": "FeedItem",
        "subjectId": record_id,
    }


def _has_cast_in_chatter(record_id):
    """Check if a CAST comment exists in the Chatter feed for a record."""
    try:
        comments = sfdc_chatter_read(record_id, page_size=20)
        for c in comments:
            if "error" in c:
                return False
            text = (c.get("text") or "").lower()
            if "context" in text and "ask" in text:
                return True
        return False
    except Exception:
        return False


def sfdc_chatter_read(record_id, page_size=5):
    """Read Chatter feed elements from an SFDC record."""
    raw = run_cmd(
        ["sf", "api", "request", "rest",
         f"/services/data/v66.0/chatter/feeds/record/{record_id}/feed-elements?pageSize={page_size}",
         "--method", "GET"],
        timeout=30,
    )
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            data = data[0] if data else {}
        elements = data.get("elements", [])
        results = []
        for el in elements:
            body = el.get("body", {})
            results.append({
                "date": el.get("createdDate", ""),
                "author": (el.get("actor") or {}).get("displayName", ""),
                "text": body.get("text", ""),
                "segments": body.get("messageSegments", []),
            })
        return results
    except Exception as e:
        return [{"error": str(e), "raw": raw[:500]}]

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def lookup_cache(query):
    output = run_cmd([sys.executable, str(CACHE_SCRIPT), "lookup", query])
    if "NOT_FOUND" in output or output.startswith("ERROR"):
        return None
    return yaml.safe_load(output)

# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

def search_calendar(query, event_ids=None):
    if not GCAL_SCRIPT:
        return "ERROR: gcal_builder.py not found"
    parts = []
    if event_ids:
        for eid in event_ids[:3]:
            out = run_cmd(
                [sys.executable, str(GCAL_SCRIPT), "get", "--event-id", eid],
                timeout=20,
            )
            if not out.startswith("ERROR"):
                parts.append(out)
    if not parts:
        out = run_cmd(
            [sys.executable, str(GCAL_SCRIPT), "search", "--query", query],
            timeout=20,
        )
        parts.append(out)
    return truncate("\n---\n".join(parts), 3000)


def find_availability(days=5):
    """Find available 30-min slots in the next N business days."""
    if not GCAL_SCRIPT:
        return "ERROR: gcal_builder.py not found"
    return run_cmd(
        [sys.executable, str(GCAL_SCRIPT), "find-availability",
         "--duration", "30", "--days", str(days)],
        timeout=20,
    )

# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------

def search_gmail(domain):
    if not GMAIL_SCRIPT or not domain:
        return None
    raw = run_cmd(
        [sys.executable, str(GMAIL_SCRIPT),
         "search", "--query", f"newer_than:30d (from:{domain} OR to:{domain})",
         "--max-results", "5"],
        timeout=30,
    )
    return truncate(raw, 3000) if not raw.startswith("ERROR") else raw

# ---------------------------------------------------------------------------
# Obsidian
# ---------------------------------------------------------------------------

def read_obsidian_asq(ar_number, account_name=""):
    """Read an ASQ page from Obsidian vault."""
    if not _obsidian_enabled():
        return None
    vault = _obsidian_vault_path()
    if not vault:
        return None
    asq_dir = vault / "ASQ" / "Active"
    if not asq_dir.exists():
        return None
    target = asq_dir / f"{ar_number} {account_name}.md"
    if target.exists():
        return truncate(target.read_text(), 5000, 800)
    for f in sorted(asq_dir.glob(f"{ar_number}*.md")):
        return truncate(f.read_text(), 5000, 800)
    return None


def patch_obsidian_asq(ar_number, heading, content, account_name=""):
    """Append content under a heading in an Obsidian ASQ file."""
    if not _obsidian_enabled():
        return "ERROR: Obsidian not enabled"
    vault = _obsidian_vault_path()
    if not vault:
        return "ERROR: Obsidian vault path not configured. Run: asq_config.py set obsidian_vault_path ~/your-vault"
    asq_dir = vault / "ASQ" / "Active"
    if not asq_dir.exists():
        return f"ERROR: ASQ directory not found: {asq_dir}"
    target = None
    if account_name:
        candidate = asq_dir / f"{ar_number} {account_name}.md"
        if candidate.exists():
            target = candidate
    if not target:
        for f in sorted(asq_dir.glob(f"{ar_number}*.md")):
            target = f
            break
    if not target:
        return f"ERROR: No Obsidian page found for {ar_number}"
    lines = target.read_text().splitlines(keepends=True)
    heading_pattern = f"## {heading}"
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip() == heading_pattern:
            insert_idx = i + 1
            break
    if insert_idx is None:
        return f"ERROR: Heading '## {heading}' not found in {target.name}"
    insert_text = f"\n{content.strip()}\n"
    lines.insert(insert_idx, insert_text)
    target.write_text("".join(lines))
    return f"OK: Appended under '## {heading}' in {target.name}"


# ---------------------------------------------------------------------------
# STS Content Index (replaces local file reading)
# ---------------------------------------------------------------------------

def get_sts_index(support_type):
    """Return the STS content index entry for a support type.

    Instead of reading local Obsidian files (which can go stale), this returns
    page titles and search queries that Claude/agents can use to fetch fresh
    content from Glean, Confluence, or Obsidian MCP.
    """
    # Exact match
    entry = STS_CONTENT_INDEX.get(support_type)
    if entry:
        return {**entry, "support_type": support_type, "cross_cutting": STS_CROSS_CUTTING}

    # Fuzzy match on keywords
    st_lower = support_type.lower()
    for stype, info in STS_CONTENT_INDEX.items():
        if stype.lower() in st_lower or st_lower in stype.lower():
            return {**info, "support_type": stype, "cross_cutting": STS_CROSS_CUTTING}
        for kw in info.get("keywords", []):
            if kw.lower() in st_lower:
                return {**info, "support_type": stype, "cross_cutting": STS_CROSS_CUTTING}

    return {
        "support_type": support_type,
        "pages": [],
        "search_query": f"STS Content Repo {support_type}",
        "keywords": [],
        "cross_cutting": STS_CROSS_CUTTING,
        "note": f"No exact index match for '{support_type}'. Use the search_query to find relevant content.",
    }


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------

def compute_flags(cache, sfdc_data):
    flags = []
    end_date_str = (cache or {}).get("end_date")
    if end_date_str:
        try:
            days = (datetime.strptime(end_date_str, "%Y-%m-%d") - datetime.now()).days
            if days < 0:
                flags.append(f"ASQ PAST end date by {abs(days)} days ({end_date_str})")
            elif days <= 14:
                flags.append(f"ASQ end date in {days} days ({end_date_str})")
        except ValueError:
            pass
    if sfdc_data and isinstance(sfdc_data, dict):
        for asq in sfdc_data.get("asqs", []):
            status = asq.get("Status__c") or ""
            if status not in ("Completed", "Cancelled"):
                record_id = asq.get("Id") or ""
                if record_id and not _has_cast_in_chatter(record_id):
                    flags.append("No CAST detected in Chatter feed — may need one")
        for uco in sfdc_data.get("ucos", []):
            if not (uco.get("Next_Steps__c") or "").strip():
                flags.append(f"UCO {uco.get('Name', '?')} has empty Next Steps")
    return flags

# ===========================================================================
# SUBCOMMAND: gather
# ===========================================================================

def cmd_gather(args):
    """Read-only context gathering from all sources."""
    sfdc_user_id = _sfdc_user_id()
    output = {"query": args.query, "timestamp": datetime.now().isoformat()}

    cache = lookup_cache(args.query)
    output["cache_hit"] = cache is not None
    output["cache"] = cache

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {}

        # SFDC
        if cache and cache.get("sfdc_id"):
            soql = (
                "SELECT Id, Name, Status__c, Support_Type__c, "
                "Request_Status_Notes__c, Request_Closure_Note__c, "
                "End_Date__c, Start_Date__c, Account__r.Name, "
                "Request_Description__c, Requestor__r.Name, "
                "CreatedBy.Name, CreatedById, LastModifiedDate "
                "FROM ApprovalRequest__c "
                f"WHERE Id = '{cache['sfdc_id']}'"
            )
        else:
            name = (cache["account_name"] if cache else args.query).replace("'", "\\'")
            soql = (
                "SELECT Id, Name, Status__c, Support_Type__c, "
                "Request_Status_Notes__c, Request_Closure_Note__c, "
                "End_Date__c, Start_Date__c, Account__r.Name, "
                "Request_Description__c, Requestor__r.Name, "
                "CreatedBy.Name, CreatedById, LastModifiedDate "
                "FROM ApprovalRequest__c "
                f"WHERE OwnerId = '{sfdc_user_id}' "
                f"AND Account__r.Name LIKE '%{name}%'"
            )

        def _query_sfdc_full():
            results = {}
            try:
                records = sfdc_query(soql)
                for r in records:
                    for field in ("Request_Status_Notes__c", "Request_Closure_Note__c", "Request_Description__c"):
                        val = r.get(field) or ""
                        r[field] = truncate(val, 3000, 200)
                results["asqs"] = records
            except Exception as e:
                results["asqs_error"] = str(e)

            acct_name = None
            if cache:
                acct_name = cache.get("account_name")
            elif results.get("asqs"):
                acct_name = (results["asqs"][0].get("Account__r") or {}).get("Name")
            if acct_name:
                try:
                    safe = acct_name.replace("'", "\\'")
                    results["ucos"] = sfdc_query(
                        f"SELECT Name, Stage__c, Next_Steps__c, Go_Live_Date__c, Account__r.Name "
                        f"FROM Use_Case_Object__c WHERE Account__r.Name LIKE '%{safe}%'"
                    )
                    for u in results.get("ucos", []):
                        u["Next_Steps__c"] = truncate(u.get("Next_Steps__c") or "", 1500, 200)
                except Exception as e:
                    results["ucos_error"] = str(e)
            return results

        futures["sfdc"] = pool.submit(_query_sfdc_full)

        # Calendar
        event_ids = None
        if cache and cache.get("known_calendar_events"):
            event_ids = [e["event_id"] for e in cache["known_calendar_events"] if e.get("event_id")]
        futures["calendar"] = pool.submit(
            search_calendar,
            cache["account_name"] if cache else args.query,
            event_ids,
        )

        # Gmail
        domain = args.domain or (cache.get("customer_email_domain") if cache else None)
        if domain:
            futures["gmail"] = pool.submit(search_gmail, domain)

        # Obsidian ASQ page
        if cache and cache.get("ar_number"):
            futures["obsidian"] = pool.submit(
                read_obsidian_asq, cache["ar_number"], cache.get("account_name", ""),
            )

        for key, future in futures.items():
            try:
                output[key] = future.result(timeout=45)
            except Exception as e:
                output[key] = f"ERROR: {e}"

    # STS Content Index (not local files — just the index for Claude to fetch)
    support_type = (cache or {}).get("support_type")
    if support_type:
        output["sts_content"] = get_sts_index(support_type)
    else:
        output["sts_content"] = None

    # Slack metadata
    if cache and cache.get("slack_channel_id"):
        output["slack"] = {
            "channel_id": cache.get("slack_channel_id"),
            "channel_name": cache.get("slack_channel_name"),
            "language": cache.get("slack_channel_language"),
        }
    else:
        output["slack"] = None

    output["flags"] = compute_flags(cache, output.get("sfdc"))

    hints = []
    if not output.get("gmail"):
        hints.append("Gmail not queried — pass --domain if needed.")
    if output.get("slack"):
        hints.append(
            f"Slack: {output['slack']['channel_name']} ({output['slack']['channel_id']}) "
            "— use conversations.history MCP to read."
        )
    if output.get("sts_content") and output["sts_content"].get("pages"):
        hints.append(
            "STS content index returned page titles — fetch fresh content via Glean search "
            f"(query: \"{output['sts_content']['search_query']}\") or Obsidian/Confluence MCP."
        )
    output["hints"] = hints

    # Include relevant preferences so the LLM skill layer can use them
    output["preferences"] = {
        "status_notes": {
            "format": _get_pref("status_notes.format"),
            "language": _get_pref("status_notes.language"),
            "order": _get_pref("status_notes.order"),
            "session_numbering": _get_pref("status_notes.session_numbering"),
            "discovery_is_numbered": _get_pref("status_notes.discovery_is_numbered"),
            "internal_sync_label": _get_pref("status_notes.internal_sync_label"),
        },
        "cast": {
            "auto_cc_manager": _get_pref("cast.auto_cc_manager"),
            "sections": _get_pref("cast.sections"),
        },
        "tone": {
            "sfdc": _get_pref("tone.sfdc"),
            "sfdc_description": _get_pref("tone.sfdc_description"),
            "slack": _get_pref("tone.slack"),
            "slack_description": _get_pref("tone.slack_description"),
        },
        "slack": {
            "channel_pattern": _get_pref("slack.channel_pattern"),
            "intro_template": _get_pref("slack.intro_template"),
            "closing_template": _get_pref("slack.closing_template"),
            "detect_language": _get_pref("slack.detect_language"),
        },
        "close_notes": {
            "format": _get_pref("close_notes.format"),
            "separator": _get_pref("close_notes.separator"),
            "partial_tag": _get_pref("close_notes.partial_tag"),
            "template": _get_pref("close_notes.template"),
        },
    }

    print(json.dumps(output, indent=2, default=str, ensure_ascii=False))

# ===========================================================================
# SUBCOMMAND: sfdc-query
# ===========================================================================

def cmd_sfdc_query(args):
    try:
        records = sfdc_query(args.soql, timeout=args.timeout)
        print(json.dumps(records, indent=2, default=str, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

# ===========================================================================
# SUBCOMMAND: sfdc-update
# ===========================================================================

def cmd_sfdc_update(args):
    result = sfdc_update(args.object_id, args.json_file)
    if result and result.startswith("ERROR"):
        print(result, file=sys.stderr)
        sys.exit(1)
    print(result if result else "OK (no content — update succeeded)")

# ===========================================================================
# SUBCOMMAND: sfdc-chatter
# ===========================================================================

def cmd_sfdc_chatter(args):
    result = sfdc_chatter(args.json_file)
    try:
        data = json.loads(result)
        if "id" in data:
            print(f"Success! Comment ID: {data['id']}")
        elif isinstance(data, list) and data and "id" in data[0]:
            print(f"Success! Comment ID: {data[0]['id']}")
        else:
            print(result[:500])
    except Exception:
        print(result[:500] if result else "OK")

# ===========================================================================
# SUBCOMMAND: cast-post
# ===========================================================================

def cmd_cast_post(args):
    """Build and post a CAST from plain text arguments.
    Default is dry-run (preview). Must pass --confirm to actually post.
    """
    timeline = [l.strip() for l in args.timeline.split("|") if l.strip()]
    cc_ids = [uid.strip() for uid in args.cc.split(",") if uid.strip()]

    # Add extra CC IDs from preferences
    extra_cc = _get_pref("cast.extra_cc_ids")
    if extra_cc:
        for uid in extra_cc.split(","):
            uid = uid.strip()
            if uid and uid not in cc_ids:
                cc_ids.append(uid)

    # Auto-CC manager (configurable via preferences)
    manager_id = _manager_sfdc_id()
    if _get_pref("cast.auto_cc_manager") and manager_id not in cc_ids:
        cc_ids.insert(0, manager_id)

    payload = build_cast_payload(
        record_id=args.record_id,
        context=args.context,
        ask=args.ask,
        success=args.success,
        timeline_lines=timeline,
        cc_ids=cc_ids,
    )

    tmp_path = "/tmp/cast_payload.json"
    with open(tmp_path, "w") as f:
        json.dump(payload, f, ensure_ascii=False)

    if not args.confirm:
        manager_name = _config().get("manager_name", "your manager")
        print("=" * 60)
        print("  DRY-RUN PREVIEW — NOTHING WAS POSTED TO SALESFORCE")
        print("=" * 60)
        print(f"\nContext:\n{args.context}\n")
        print(f"Ask:\n{args.ask}\n")
        print(f"Success:\n{args.success}\n")
        print("Timeline:")
        for line in timeline:
            bullet = line if line.startswith("- ") else f"- {line}"
            print(f"  {bullet}")
        print(f"\nC/C: {', '.join(cc_ids)} (manager: {manager_name})")
        print(f"\nTarget: {args.record_id}")
        print(f"Payload saved to: {tmp_path}")
        print()
        print("=" * 60)
        print("  WARNING: THIS CAST HAS *NOT* BEEN POSTED.")
        print("  No data was written to Salesforce.")
        print("  To post, re-run this command with --confirm.")
        print("=" * 60)
        return

    result = sfdc_chatter(tmp_path)
    try:
        data = json.loads(result)
        if "id" in data:
            print(f"Success! Comment ID: {data['id']}")
        elif isinstance(data, list) and data and "id" in data[0]:
            print(f"Success! Comment ID: {data[0]['id']}")
        else:
            print(result[:500])
    except Exception:
        print(result[:500] if result else "OK")

# ===========================================================================
# SUBCOMMAND: sfdc-chatter-read
# ===========================================================================

def cmd_sfdc_chatter_read(args):
    results = sfdc_chatter_read(args.record_id, args.limit)
    print(json.dumps(results, indent=2, default=str, ensure_ascii=False))

# ===========================================================================
# SUBCOMMAND: obsidian-patch
# ===========================================================================

def cmd_obsidian_patch(args):
    result = patch_obsidian_asq(args.ar_number, args.heading, args.content, args.account or "")
    print(result)
    if result.startswith("ERROR"):
        sys.exit(1)

# ===========================================================================
# SUBCOMMAND: discover-new
# ===========================================================================

def cmd_discover_new(args):
    sfdc_user_id = _sfdc_user_id()
    soql = (
        "SELECT Id, Name, Status__c, Account__r.Name, Request_Description__c, "
        "Support_Type__c, Resource__r.Name, Requestor__r.Name, "
        "Start_Date__c, End_Date__c, Request_Status_Notes__c, "
        "LastModifiedDate, CreatedBy.Name, CreatedById "
        "FROM ApprovalRequest__c "
        f"WHERE OwnerId = '{sfdc_user_id}' "
        "AND Status__c = 'In Progress' "
        "AND (Request_Status_Notes__c = null OR Request_Status_Notes__c = '') "
        "ORDER BY CreatedDate DESC"
    )
    try:
        records = sfdc_query(soql)
        for r in records:
            ar = r.get("Name", "")
            cached = lookup_cache(ar)
            r["_cached"] = cached is not None
        output = {
            "count": len(records),
            "asqs": records,
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(output, indent=2, default=str, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

# ===========================================================================
# SUBCOMMAND: list-active
# ===========================================================================

def cmd_list_active(args):
    sfdc_user_id = _sfdc_user_id()
    soql = (
        "SELECT Id, Name, Status__c, Support_Type__c, "
        "Account__r.Name, End_Date__c, Start_Date__c, "
        "Request_Status_Notes__c, CreatedBy.Name, CreatedById, "
        "LastModifiedDate "
        "FROM ApprovalRequest__c "
        f"WHERE OwnerId = '{sfdc_user_id}' "
        "AND Status__c NOT IN ('Complete','Rejected','Cancelled') "
        "ORDER BY End_Date__c ASC NULLS LAST"
    )
    try:
        records = sfdc_query(soql, timeout=45)
        now = datetime.now()
        for r in records:
            ar = r.get("Name", "")
            cached = lookup_cache(ar)
            r["_cached"] = cached is not None
            r["_slack_channel"] = cached.get("slack_channel_name") if cached else None
            r["_slack_language"] = cached.get("slack_channel_language") if cached else None
            end = r.get("End_Date__c")
            if end:
                try:
                    r["_days_remaining"] = (datetime.strptime(end, "%Y-%m-%d") - now).days
                except ValueError:
                    r["_days_remaining"] = None
            notes = r.get("Request_Status_Notes__c") or ""
            r["_has_cast"] = _has_cast_in_chatter(r.get("Id", "")) if r.get("Id") else False
            r["Request_Status_Notes__c"] = notes[:300] + ("..." if len(notes) > 300 else "")
        print(json.dumps({"count": len(records), "asqs": records,
                          "timestamp": now.isoformat()},
                         indent=2, default=str, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

# ===========================================================================
# SUBCOMMAND: close
# ===========================================================================

# Extra required fields by support type for closing
CLOSING_EXTRA_FIELDS = {
    "Platform Administration": {
        "Private_Connectivity_Type__c": [
            "Not Applicable / No Private Connectivity",
            "AWS - Backend PL (New Wokspace)", "AWS - Frontend PL (New Workspace)",
            "AWS - Full PL (New Wokspace)", "AWS - Backend PL (Existing Wokspace)",
            "AWS - Frontend PL (Existing Wokspace)", "AWS - Full PL (Existing Wokspace)",
            "GCP - Backend PSC (New Workspace)", "GCP - Frontend PSC (New Workspace)",
            "GCP - Full PSC (New Wokspace)", "GCP - Backend PSC (Existing Workspace)",
            "GCP - Frontend PSC (Existing Workspace)", "GCP - Full PSC (Existing Workspace)",
            "Azure - Back-end only (New Wokspace)", "Azure - Front-end hybrid (New Workspace)",
            "Azure - End-to-end Private (New Wokspace)", "Azure - Back-end only (Existing Wokspace)",
            "Azure - Front-end hybrid  (Existing Wokspace)", "Azure - End-to-end Private(Existing Wokspace)",
        ],
        "Platform_Configuration_Options__c": [
            "None Applies", "Custom DNS", "Customer Managed Keys",
            "Compliance Security Profile", "IP Access List - Account Level",
            "IP Access List - Workspace Level",
        ],
    },
}


def cmd_close(args):
    """Prepare and validate ASQ closing payload."""
    cached = lookup_cache(args.query)
    if not cached:
        print(f"ERROR: No cached ASQ found for '{args.query}'", file=sys.stderr)
        sys.exit(1)

    sfdc_id = cached.get("sfdc_id")
    support_type = cached.get("support_type", "")
    ar_number = cached.get("ar_number")

    payload = {
        "Status__c": "Complete",
        "Actual_Completion_Date__c": datetime.now().strftime("%Y-%m-%d"),
    }
    if args.partial:
        payload["PartiallyComplete__c"] = True

    extra = CLOSING_EXTRA_FIELDS.get(support_type, {})
    missing = []
    for field, valid_values in extra.items():
        cli_key = field.lower().replace("__c", "")
        val = getattr(args, cli_key, None)
        if val:
            payload[field] = val
        else:
            missing.append({"field": field, "valid_values": valid_values})

    # Genie Room from config
    genie_rooms = _genie_rooms()
    genie_room = genie_rooms.get(support_type, genie_rooms.get("default", ""))

    # STS content index for outcome comparison
    sts_index = get_sts_index(support_type) if support_type else None

    output = {
        "ar_number": ar_number,
        "sfdc_id": sfdc_id,
        "support_type": support_type,
        "payload": payload,
        "missing_fields": missing,
        "genie_room_id": genie_room,
        "sts_content_index": sts_index,
        "closing_instructions": (
            "Use the genie_room_id to query consumption metrics for this ASQ. "
            "Use sts_content_index to fetch the expected outcomes for this support type, "
            "then compare actual results against those expectations in the STAR close notes."
        ),
    }
    print(json.dumps(output, indent=2, default=str, ensure_ascii=False))
    if missing:
        print(f"\nWARNING: {len(missing)} required field(s) missing for '{support_type}' closures.", file=sys.stderr)
        sys.exit(2)

# ===========================================================================
# SUBCOMMAND: sfdc-batch-update
# ===========================================================================

def cmd_sfdc_batch_update(args):
    with open(args.json_file) as f:
        items = json.load(f)
    results = []
    for item in items:
        obj_id = item["id"]
        fields = item["fields"]
        tmp = f"/tmp/asq_batch_{obj_id}.json"
        with open(tmp, "w") as f:
            json.dump(fields, f, ensure_ascii=False)
        result = sfdc_update(obj_id, tmp)
        success = not (result and result.startswith("ERROR"))
        results.append({"id": obj_id, "success": success, "result": result or "OK"})
    print(json.dumps({"total": len(items), "results": results}, indent=2))
    if any(not r["success"] for r in results):
        sys.exit(1)

# ===========================================================================
# SUBCOMMAND: obsidian-read
# ===========================================================================

def cmd_obsidian_read(args):
    content = read_obsidian_asq(args.query, args.account or "")
    if not content:
        vault = _obsidian_vault_path()
        if vault:
            asq_dir = vault / "ASQ" / "Active"
            if asq_dir.exists():
                q = args.query.lower()
                for f in sorted(asq_dir.glob("*.md")):
                    if q in f.stem.lower():
                        content = truncate(f.read_text(), 5000, 800)
                        break
    if content:
        print(content)
    else:
        print(f"NOT_FOUND: No Obsidian page matches '{args.query}'")
        sys.exit(1)

# ===========================================================================
# SUBCOMMAND: sts-index
# ===========================================================================

def cmd_sts_index(args):
    """Print the STS content index for a support type (or all)."""
    if args.support_type:
        entry = get_sts_index(args.support_type)
        print(json.dumps(entry, indent=2))
    else:
        print(json.dumps({
            "index": STS_CONTENT_INDEX,
            "cross_cutting": STS_CROSS_CUTTING,
        }, indent=2))

# ===========================================================================
# SUBCOMMAND: availability
# ===========================================================================

def cmd_availability(args):
    result = find_availability(args.days)
    print(result)

# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="ASQ Tools — unified CLI for ASQ operations")
    sub = parser.add_subparsers(dest="command", required=True)

    # gather
    p = sub.add_parser("gather", help="Read-only context gathering from all sources")
    p.add_argument("query", help="Customer name, AR number, or alias")
    p.add_argument("--domain", help="Customer email domain for Gmail")
    p.set_defaults(func=cmd_gather)

    # sfdc-query
    p = sub.add_parser("sfdc-query", help="Run a SOQL query")
    p.add_argument("soql", help="SOQL query string")
    p.add_argument("--timeout", type=int, default=30)
    p.set_defaults(func=cmd_sfdc_query)

    # sfdc-update
    p = sub.add_parser("sfdc-update", help="PATCH an SFDC record")
    p.add_argument("object_id", help="SFDC record ID")
    p.add_argument("json_file", help="Path to JSON file with update payload")
    p.set_defaults(func=cmd_sfdc_update)

    # sfdc-chatter
    p = sub.add_parser("sfdc-chatter", help="Post a raw Chatter payload from a JSON file")
    p.add_argument("json_file", help="Path to JSON file with Chatter payload")
    p.set_defaults(func=cmd_sfdc_chatter)

    # cast-post
    p = sub.add_parser("cast-post", help="Build and post a CAST (dry-run by default)")
    p.add_argument("record_id", help="SFDC ASQ record ID")
    p.add_argument("--context", required=True, help="Context section text")
    p.add_argument("--ask", required=True, help="Ask section text")
    p.add_argument("--success", required=True, help="Success section text")
    p.add_argument("--timeline", required=True,
                   help="Timeline bullets separated by |")
    p.add_argument("--cc", default="",
                   help="Comma-separated SFDC user IDs to CC (manager always included)")
    p.add_argument("--confirm", action="store_true",
                   help="Actually post (without this, only previews)")
    p.set_defaults(func=cmd_cast_post)

    # sfdc-chatter-read
    p = sub.add_parser("sfdc-chatter-read", help="Read Chatter feed from an SFDC record")
    p.add_argument("record_id", help="SFDC record ID")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=cmd_sfdc_chatter_read)

    # obsidian-patch
    p = sub.add_parser("obsidian-patch", help="Append content under a heading in Obsidian")
    p.add_argument("ar_number", help="AR number")
    p.add_argument("heading", help="Heading to append under")
    p.add_argument("content", help="Content to append")
    p.add_argument("--account", help="Account name")
    p.set_defaults(func=cmd_obsidian_patch)

    # list-active
    p = sub.add_parser("list-active", help="List all active ASQs for weekly review")
    p.set_defaults(func=cmd_list_active)

    # close
    p = sub.add_parser("close", help="Prepare and validate ASQ closing payload")
    p.add_argument("query", help="AR number, account name, or alias")
    p.add_argument("--partial", action="store_true", help="Mark as partially complete")
    p.add_argument("--private_connectivity_type", help="Required for Platform Admin closures")
    p.add_argument("--platform_configuration_options", help="Required for Platform Admin closures")
    p.set_defaults(func=cmd_close)

    # sfdc-batch-update
    p = sub.add_parser("sfdc-batch-update", help="Batch PATCH multiple SFDC records")
    p.add_argument("json_file", help="JSON file: [{id, fields}, ...]")
    p.set_defaults(func=cmd_sfdc_batch_update)

    # discover-new
    p = sub.add_parser("discover-new", help="Find new ASQs for onboarding")
    p.set_defaults(func=cmd_discover_new)

    # obsidian-read
    p = sub.add_parser("obsidian-read", help="Read Obsidian ASQ page")
    p.add_argument("query", help="AR number or account name")
    p.add_argument("--account", help="Account name")
    p.set_defaults(func=cmd_obsidian_read)

    # sts-index
    p = sub.add_parser("sts-index", help="Print STS content index")
    p.add_argument("support_type", nargs="?", help="Support type to look up (omit for all)")
    p.set_defaults(func=cmd_sts_index)

    # availability
    p = sub.add_parser("availability", help="Find calendar availability")
    p.add_argument("--days", type=int, default=5)
    p.set_defaults(func=cmd_availability)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
