# Reference Data Cache Setup

The STS service scope and competency matrix are cached locally at `~/asq-local-cache/triage/` with a 7-day TTL. This avoids re-fetching from Google APIs on every triage run.

## Cache Structure

```
~/asq-local-cache/triage/
├── sts_service_scope.md          # Converted from Google Slides
├── competency_matrix.json        # Raw Sheets API response
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
meta_path.write_text('\n'.join(f'{k}: {v}' for k, v in meta.items()) + '\n')
"
```
