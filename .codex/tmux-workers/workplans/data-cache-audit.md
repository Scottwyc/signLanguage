# Codex Tmux Worker Plan - data-cache-audit

Created: 2026-05-20T17:16:12+08:00
Session: signlanguage-scoring-workers
Window: cw-data-cache-audit
Working directory: /data/WYC/signLanguage
Model: gpt-5.5
Reasoning effort: xhigh

## Task

You are Worker data-cache-audit in a tmux-launched Codex process.

Goal: inspect the current /data/WYC/signLanguage project state and identify reusable existing artifacts for the scoring MVP line.

Working directory: /data/WYC/signLanguage

Write scope:
- Write only your report at /data/WYC/signLanguage/work/reports/scoring_data_cache_audit_20260520_draft.md
- You may update your assigned progress/report files under /data/WYC/signLanguage/.codex/tmux-workers/

Do not modify:
- Source scripts
- Existing worklog files
- Existing generated artifacts
- Other scoring report drafts

Use these constraints:
- Current project has no real user video stream samples and no human score labels.
- Treat existing demo videos and cached Holistic JSON as assets for offline sanity checks only.
- Prefer exact paths and concise evidence over broad speculation.

Tasks:
1. Inventory current demo videos and existing Holistic/cache/result files that can seed a scoring prototype.
2. Identify which files are raw dense or step-dense Holistic JSON versus selected keyframe outputs or visualizations.
3. Summarize missing data for a real scoring dataset.
4. Propose a minimal reusable data layout for standard templates and pseudo-user sanity-check cases.
5. Write a Chinese draft report to your owned path with timestamp, inspected paths, evidence, risks, and next recommendations.

Return: changed files, commands run, key findings, blockers, and next recommendation.

## Write Scope

- report:/data/WYC/signLanguage/work/reports/scoring_data_cache_audit_20260520_draft.md

## Owned Paths

- /data/WYC/signLanguage/work/reports/scoring_data_cache_audit_20260520_draft.md

## Resources

- cpu:data-audit

## Git Isolation

- Shared working tree.

## Inbox

/data/WYC/signLanguage/.codex/tmux-workers/inbox/data-cache-audit

## Background Job Registry

/data/WYC/signLanguage/.codex/tmux-workers/jobs/data-cache-audit.json

Register background jobs with:

```bash
python /home/wuyangcheng/.codex/skills/general/tmux-codex-parallel-workers/scripts/codex_tmux_manager.py --state-dir /data/WYC/signLanguage/.codex/tmux-workers --session signlanguage-scoring-workers job-add data-cache-audit --pid <PID> --name <job-name> --log <log-path> --command '<command>'
```

## Coordinator Notes

None.

## Required Completion Report

- Changed files, if any
- Commands run
- Result or metric evidence
- Blockers
- Next recommended action
