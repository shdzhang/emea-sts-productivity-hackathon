# Reference Data Cache Setup

The STS service scope and competency matrix are cached locally at `~/asq-local-cache/triage/` with a 7-day TTL. This avoids re-fetching from Google APIs on every triage run.

## Cache Structure

```
~/asq-local-cache/triage/
├── sts_service_scope.md          # Converted from Google Slides
├── competency_matrix.json        # Raw Sheets API response
├── team_member_ids.json          # Pre-resolved SFDC User IDs for team members
└── cache_meta.yaml               # Timestamps for TTL checks (simple key: value format)
```

## Cache Freshness Check

```bash
mkdir -p ~/asq-local-cache/triage

python3 << 'PYEOF'
import json
from datetime import datetime
from pathlib import Path

meta_path = Path.home() / "asq-local-cache" / "triage" / "cache_meta.yaml"
if meta_path.exists():
    meta = {}
    for line in meta_path.read_text().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("'\"")
    now = datetime.now()
    for key in ["service_scope_fetched", "competency_matrix_fetched"]:
        ts = meta.get(key, "2000-01-01")
        age = (now - datetime.fromisoformat(ts)).days
        print(f"{key}: {age} days old {'(STALE)' if age > 7 else '(fresh)'}")
else:
    print("No cache_meta.yaml — all caches need fetching")
PYEOF
```

If the user says **"refresh"** or **"force refresh"**, skip the cache check and re-fetch both sources.

## STS Service Scope (Google Slides → cached markdown)

**Source**: `https://docs.google.com/presentation/d/1EcxZB5Q5bT3waYUMDM72OcxCEpz6XaXtmJzzPqwSu0E/edit`

If `sts_service_scope.md` is missing or older than 7 days:

1. Export the deck using the `google-ppt2md` skill's drive_export script:
   ```bash
   PPTMD_DIR=~/.claude/plugins/cache/fe-vibe/fe-google-tools/*/skills/google-ppt2md
   uv run python3 $PPTMD_DIR/resources/drive_export.py "https://docs.google.com/presentation/d/1EcxZB5Q5bT3waYUMDM72OcxCEpz6XaXtmJzzPqwSu0E/edit"
   ```
   This outputs JSON: `{"path": "/tmp/<name>/<name>.json", "name": "<name>"}`.

2. Convert to markdown (text-only, no images needed for triage):
   ```bash
   cd ~/asq-local-cache/triage
   uv run python3 $PPTMD_DIR/resources/ppt2md.py "<path from step 1>" --no-images
   ```
   > **Important**: `ppt2md.py` writes output to a **subdirectory** named after the file (e.g., `./Shared_Technical_Services__gosts/Shared_Technical_Services__gosts.md`). It does NOT write to a predictable filename.

3. Copy the output to the standard cache location:
   ```bash
   cp ~/asq-local-cache/triage/Shared_Technical_Services__gosts/Shared_Technical_Services__gosts.md \
      ~/asq-local-cache/triage/sts_service_scope.md
   ```

4. If the `uv run` step fails (e.g., PyPI unreachable), try without `uv run` — the script may already have its dependencies available:
   ```bash
   python3 $PPTMD_DIR/resources/ppt2md.py "<path from step 1>" --no-images
   ```

5. If google-auth is expired, run `/google-auth` first, then retry.

## UC Stage Requirement Validation (Post-fetch)

After fetching the STS service scope deck, scan the cached `sts_service_scope.md` for any slides or sections mentioning UC stage requirements (look for patterns like "U2+", "U3+", "U4+", "When to engage", stage requirements). Compare what the deck says against the rules in `references/triage-rules.md` (Use Case Stage Requirements table).

**What to check:**
1. Search `sts_service_scope.md` for stage requirement patterns: `U[0-9]+\+`, "when to engage", "minimum stage"
2. For each service category found, compare the deck's stage requirement against `triage-rules.md`
3. If any mismatch is found:
   - **Print a clear WARNING** listing the service, deck value, and skill value
   - **Ask the user** whether to update `triage-rules.md` to match the deck
   - Do NOT silently proceed with outdated rules

**Example output:**
```
UC Stage Validation:
  Customer Onboarding (LA, WS, Genie): Deck says U3+, skill says U3+ ✓
  Migrations (Lakebridge, AI/BI):      Deck says U2+, skill says U2+ ✓
  Production Readiness (others):       Deck says U4+, skill says U4+ ✓
```

Or if a mismatch is found:
```
⚠ UC STAGE MISMATCH DETECTED:
  Migrations: Deck says U2+, skill says U3+ ← OUTDATED
  → Update triage-rules.md? (y/n)
```

> **Why this matters**: The go/sts deck is the source of truth for engagement rules. If the deck is updated (e.g., a service category's minimum stage changes), the skill must reflect that. Incorrect stage rules cause ASQs to be wrongly held back or wrongly assigned.

## Competency Matrix (Google Sheets → cached JSON)

**Source**: `https://docs.google.com/spreadsheets/d/1vn6LmBVBlthTvyNDJpJLIryIfSy1pU6mN7wFXYobaWE/edit` (sheet: "EMEA SME")

If `competency_matrix.json` is missing or older than 7 days:

```bash
TOKEN=$(python3 $GOOGLE_AUTH token)
SHEET_ID="1vn6LmBVBlthTvyNDJpJLIryIfSy1pU6mN7wFXYobaWE"

curl -s "https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values:batchGet?ranges=EMEA+SME!A1:Z50" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-goog-user-project: gcp-sandbox-field-eng" \
  -o ~/asq-local-cache/triage/competency_matrix.json
```

> **Important**: Use `EMEA+SME` (plus sign), NOT `EMEA%20SME`. The `%20` encoding gets double-escaped by the shell and produces an "Unable to parse range" error.

Verify the response is valid (not an error):
```bash
python3 -c "import json; d=json.load(open('$HOME/asq-local-cache/triage/competency_matrix.json')); assert 'valueRanges' in d, f'API error: {d}'; print('OK:', len(d['valueRanges'][0]['values']), 'rows')"
```

If the response contains `"error"` instead of `"valueRanges"`, google-auth is expired — run `/google-auth` first, then retry.

**Parsing the matrix:**
- `valueRanges[0].values[0][1:]` → team member names
- `valueRanges[0].values[3:23]` → service rows (col 0 = service name, col 1+ = ratings)
- `valueRanges[0].values[28][1:]` → start dates (tenure)
- Ratings are strings: "Experienced", "Intermediate", "Beginner", "No Experience", or empty

## Team Member ID Resolution (Post-fetch)

After fetching the competency matrix, resolve all team member names to their **internal** Salesforce User IDs. This avoids name-based lookups at triage time, which can match portal/customer users instead of Databricks employees.

```bash
python3 << 'PYEOF'
import json, subprocess, sys
from pathlib import Path

cache_dir = Path.home() / "asq-local-cache" / "triage"
matrix_path = cache_dir / "competency_matrix.json"
ids_path = cache_dir / "team_member_ids.json"

# 1. Extract team member names from the matrix
matrix = json.load(open(matrix_path))
names = [n.strip() for n in matrix["valueRanges"][0]["values"][0][1:] if n.strip()]
print(f"Resolving {len(names)} team member names...")

# 2. Query each name individually (handles Unicode/diacritics safely)
ASQ_TOOLS = list(Path.home().glob(".claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_tools.py"))[0]
team_ids = {}
warnings = []

for name in names:
    escaped = name.replace("'", "\\'")
    query = f"SELECT Id, Name, Email FROM User WHERE Name = '{escaped}' AND UserType = 'Standard' AND IsActive = true"
    result = subprocess.run(
        ["python3", str(ASQ_TOOLS), "sfdc-query", query],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
        # sfdc-query returns a plain JSON array, not {"records": [...]}
        records = data if isinstance(data, list) else data.get("records", [])
    except (json.JSONDecodeError, KeyError):
        warnings.append(f"  WARNING: SOQL parse error for '{name}'")
        continue

    if len(records) == 1:
        r = records[0]
        team_ids[name] = {"id": r["Id"], "email": r["Email"]}
    elif len(records) == 0:
        warnings.append(f"  WARNING: No internal user found for '{name}'")
    else:
        # Multiple matches — pick the @databricks.com one
        db_users = [r for r in records if r.get("Email", "").endswith("@databricks.com")]
        if len(db_users) == 1:
            r = db_users[0]
            team_ids[name] = {"id": r["Id"], "email": r["Email"]}
        else:
            warnings.append(f"  WARNING: {len(records)} matches for '{name}': {[r['Email'] for r in records]}")

# 3. Write the cache
json.dump(team_ids, open(ids_path, "w"), indent=2)
print(f"Resolved {len(team_ids)}/{len(names)} team members → {ids_path}")
for w in warnings:
    print(w)
PYEOF
```

If any names produce warnings, investigate manually — the name in the Google Sheet may not match the Salesforce display name exactly.

## Updating cache_meta.yaml

After any fetch, write/update the metadata. Uses simple `key: value` format (no PyYAML dependency):

```bash
python3 -c "
from datetime import datetime
from pathlib import Path
meta_path = Path.home() / 'asq-local-cache' / 'triage' / 'cache_meta.yaml'
lines = meta_path.read_text().splitlines() if meta_path.exists() else []
meta = {}
for line in lines:
    if ':' in line:
        k, v = line.split(':', 1)
        meta[k.strip()] = v.strip()
# Update whichever source was just fetched:
# meta['service_scope_fetched'] = datetime.now().isoformat()
# meta['competency_matrix_fetched'] = datetime.now().isoformat()
# meta['team_member_ids_fetched'] = datetime.now().isoformat()
meta_path.write_text('\n'.join(f'{k}: {v}' for k, v in meta.items()) + '\n')
"
```
