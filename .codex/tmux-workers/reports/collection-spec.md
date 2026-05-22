# Codex Tmux Worker Report - collection-spec

Created: 2026-05-20T17:16:19+08:00
Task: You are Worker collection-spec in a tmux-launched Codex process.

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
Session: signlanguage-scoring-workers:cw-collection-spec

## Summary

Pending worker updates.

## Evidence

Pending.

## Completion

Pending.
