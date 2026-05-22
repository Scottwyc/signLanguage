# Codex Tmux Worker Plan - collection-spec

Created: 2026-05-20T17:16:19+08:00
Session: signlanguage-scoring-workers
Window: cw-collection-spec
Working directory: /data/WYC/signLanguage
Model: gpt-5.5
Reasoning effort: xhigh

## Task

You are Worker collection-spec in a tmux-launched Codex process.

Goal: draft a standard data collection protocol for the signLanguage scoring MVP.

Working directory: /data/WYC/signLanguage

Write scope:
- Write only /data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md
- You may update your assigned progress/report files under /data/WYC/signLanguage/.codex/tmux-workers/

Do not modify:
- Source scripts
- Existing worklogs
- Existing generated artifacts
- Other scoring report drafts

Use these constraints:
- No real user video stream samples exist yet, so this protocol should define how to collect them.
- The scoring system will store raw videos, metadata, dense Holistic JSON, quality reports, and optionally keyframe selections.
- The MVP is based on MediaPipe Holistic, so include quality gates for pose/hand/face coverage and action completeness.

Tasks:
1. Specify per-word sample count recommendations for standard samples, practice/user samples, and validation samples.
2. Specify recording rules: camera position, distance, frame rate, resolution, lighting, background, clothing/occlusion, and repeat count.
3. Specify action start/end annotation rules and acceptable clip trimming policy.
4. Define metadata fields and standard-sample library versioning.
5. Define quality-control metrics and reject/warn thresholds as draft values, clearly marking them as provisional.
6. Write a Chinese draft report to your owned path with clear sections and implementation notes.

Return: changed files, commands run, key findings, blockers, and next recommendation.

## Write Scope

- report:/data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md

## Owned Paths

- /data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md

## Resources

- cpu:collection-spec

## Git Isolation

- Shared working tree.

## Inbox

/data/WYC/signLanguage/.codex/tmux-workers/inbox/collection-spec

## Background Job Registry

/data/WYC/signLanguage/.codex/tmux-workers/jobs/collection-spec.json

Register background jobs with:

```bash
python /home/wuyangcheng/.codex/skills/general/tmux-codex-parallel-workers/scripts/codex_tmux_manager.py --state-dir /data/WYC/signLanguage/.codex/tmux-workers --session signlanguage-scoring-workers job-add collection-spec --pid <PID> --name <job-name> --log <log-path> --command '<command>'
```

## Coordinator Notes

None.

## Required Completion Report

- Changed files, if any
- Commands run
- Result or metric evidence
- Blockers
- Next recommended action
