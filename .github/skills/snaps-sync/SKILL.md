---
name: launchpad-snaps-sync
description: "Manage SNAPS recipe coverage in bin/process_snaps.py against Launchpad (~mir-team/+snaps): detect missing/extra recipes, add missing entries, remove stale entries, and re-validate."
---

# Launchpad to SNAPS Sync

Use this skill to keep recipe entries in `SNAPS` aligned with Launchpad.

## Steps

1. Fetch `https://launchpad.net/~mir-team/+snaps`.
2. Extract Launchpad recipe slugs from `/~mir-team/+snap/<name>` links.
3. Extract all `"recipe": "..."` values from `bin/process_snaps.py`.
4. Diff the two sets and identify:
- `Launchpad recipes not in SNAPS` (candidates to add)
- `SNAPS recipes not found on Launchpad page` (candidates to remove)
5. Add missing entries in `SNAPS` under the correct snap/channel block.
6. Remove stale entries from `SNAPS` that no longer exist on Launchpad.
7. Re-run the diff command and confirm both mismatch lists are empty (or document accepted exceptions).

## Add Entry Guidelines

1. Add the new channel key in the correct snap section, for example `"26/beta"`.
2. Set the recipe exactly as listed on Launchpad.
3. If the entry uses a PPA (`"ppa": "rc"` or `"ppa": "dev"`) and should not use default from `DEFAULT_RELEASE`, set `"release"` explicitly.

## Remove Entry Guidelines

1. Remove only the stale channel entry first.
2. If a snap block becomes empty, remove the empty snap block.
3. Re-run the diff command and check for unintended drift.

## Output Format

Return a short list of additions, removals, and summary counts.
