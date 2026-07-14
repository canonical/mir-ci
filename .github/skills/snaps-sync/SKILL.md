---
name: launchpad-snaps-sync
description: 'Manage SNAPS recipe coverage in bin/process_snaps.py against Launchpad (~mir-team/+snaps): detect missing/extra recipes, add missing entries, remove stale entries, and re-validate.'
---

# Launchpad to SNAPS Sync

Use this skill to keep recipe entries in `SNAPS` aligned with Launchpad.

## Steps

1. Fetch `https://launchpad.net/~mir-team/+snaps`.
1. Extract Launchpad recipe slugs from `/~mir-team/+snap/<name>` links.
1. Extract all `"recipe": "..."` values from `bin/process_snaps.py`.
1. Diff the two sets and identify:
   - `Launchpad recipes not in SNAPS` (candidates to add)
   - `SNAPS recipes not found on Launchpad page` (candidates to remove)
1. Add missing entries in `SNAPS` under the correct snap/channel block.
1. Remove stale entries from `SNAPS` that no longer exist on Launchpad.
1. Re-run the diff command and confirm both mismatch lists are empty (or document accepted exceptions).

## Add Entry Guidelines

1. Add the new channel key in the correct snap section, for example `"26/beta"`.
1. Set the recipe exactly as listed on Launchpad.
1. If the entry uses a PPA (`"ppa": "rc"` or `"ppa": "dev"`) and should not use default from `DEFAULT_RELEASE`, set `"release"` explicitly.

## Remove Entry Guidelines

1. Remove only the stale channel entry first.
1. If a snap block becomes empty, remove the empty snap block.
1. Re-run the diff command and check for unintended drift.

## Output Format

Return a short list of additions, removals, and summary counts.
