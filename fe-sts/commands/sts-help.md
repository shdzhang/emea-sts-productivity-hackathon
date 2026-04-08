# STS Plugin — Getting Started

Welcome to the STS (Shared Technical Services) plugin for Claude Code. This plugin helps you manage ASQ (Account Specialist Request) engagements end-to-end.

## Usage

```
/sts-help
```

## Task

1. **Read user preferences** to determine their language:
   ```bash
   python3 ~/.claude/plugins/cache/fe-vibe/fe-sts/*/skills/asq-local-cache/resources/asq_config.py preferences-show user 2>/dev/null
   ```
   If `user.language` is set to something other than `en-us`, respond in that language for the rest of this interaction.

2. **Check if first-time setup is needed:**
   ```bash
   cat ~/asq-local-cache/user_config.yaml 2>/dev/null
   ```
   If the file doesn't exist or is missing `sfdc_user_id`, tell the user they need to run initial setup first and invoke the `asq-local-cache` skill.

3. **Present the plugin overview** as a concise, friendly message:

   **Available Skills:**

   | Skill | What it does | How to trigger |
   |-------|-------------|----------------|
   | **asq-update** | Update SFDC status notes, post Slack updates, write CASTs | Share meeting notes or say "update ASQ" |
   | **asq-onboarding** | Set up new ASQs — Slack channels, intro messages, SFDC notes | Say "new ASQs" or "onboard ASQs" |
   | **asq-close** | Close ASQs with STAR-format notes and consumption metrics | Say "close ASQ" or "wrap up" |
   | **asq-refresher** | Meeting prep — pulls context from SFDC, Slack, Gmail, Calendar | Say "prep me for [customer]" or "next meeting" |
   | **asq-local-cache** | Manage your local cache and preferences | Say "configure ASQ cache" |

   **Quick Commands:**
   - `/sts-help` — This guide (you're here)
   - `/sts-config` — View and change your preferences

   **Configuration:**
   Your preferences live in `~/asq-local-cache/preferences.yaml`. Key settings:
   - `user.language` — Language for Claude's responses (en-us, pt-br, es, etc.)
   - `status_notes.language` — Language for SFDC notes (always en-us for consistency)
   - `tone.slack` — Slack message tone (friendly, professional)
   - `cast.*` — CAST formatting, CC rules, timeline structure

   To change a preference:
   ```
   Tell Claude: "set my language to pt-br" or "change slack tone to professional"
   ```

   **Custom Triggers (any language):**
   Skills are triggered by natural language — Claude understands intent regardless of language. If you find that a specific phrase in your language isn't routing to the right skill, just ask Claude:

   > "From now on, when I say '[your phrase]', use the asq-update skill."

   Claude will add this as a routing rule to your `~/.claude/CLAUDE.md`, which persists across sessions. You can also store your custom trigger phrases in preferences for reference:
   ```
   Tell Claude: "set triggers.asq-refresher to 'próxima reunião, preparar reunião'"
   ```

4. **Ask the user** what they'd like to do next. Suggest common starting points:
   - "I have meeting notes to log"
   - "Check for new ASQ assignments"
   - "Prep me for my next meeting"
   - "Show my active ASQs"
