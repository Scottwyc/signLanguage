# Codex Tmux Worker Plan - scoring-design

Created: 2026-05-20T17:16:24+08:00
Session: signlanguage-scoring-workers
Window: cw-scoring-design
Working directory: /data/WYC/signLanguage
Model: gpt-5.5
Reasoning effort: xhigh

## Task

You are Worker scoring-design in a tmux-launched Codex process.

Goal: design the first scoring mechanism for the signLanguage MVP.

Working directory: /data/WYC/signLanguage

Write scope:
- Write only /data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md
- You may update your assigned progress/report files under /data/WYC/signLanguage/.codex/tmux-workers/

Do not modify:
- Source scripts
- Existing worklogs
- Existing generated artifacts
- Other scoring report drafts

Use these constraints:
- Current phase lacks real user samples and human labels.
- Do not claim calibrated pass/fail scores.
- Dense Holistic time-series matching is the primary MVP direction; keyframe scoring is a compressed/diagnostic branch.
- Existing project logic separates candidate generation, selection, and visualization; do not reintroduce repeated Holistic runs.

Tasks:
1. Design preprocessing: coordinate normalization, scale alignment, left/right hand handling, visibility/missing-point logic.
2. Design temporal alignment: DTW baseline, segmented DTW, and keyframe-anchor alignment, with when to use each.
3. Design per-joint/per-group errors for hands, wrists, elbows/shoulders, torso, and face.
4. Design component scores: total score, hand action score, posture score, rhythm/tempo score, completion/confidence score.
5. Define diagnostic outputs: worst time ranges, worst joint groups, missing-data warnings, and visualization artifacts.
6. Write a Chinese draft report to your owned path, clearly separating prototype metrics from future calibrated scoring.

Return: changed files, commands run, key findings, blockers, and next recommendation.

## Write Scope

- report:/data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md

## Owned Paths

- /data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md

## Resources

- cpu:scoring-design

## Git Isolation

- Shared working tree.

## Inbox

/data/WYC/signLanguage/.codex/tmux-workers/inbox/scoring-design

## Background Job Registry

/data/WYC/signLanguage/.codex/tmux-workers/jobs/scoring-design.json

Register background jobs with:

```bash
python /home/wuyangcheng/.codex/skills/general/tmux-codex-parallel-workers/scripts/codex_tmux_manager.py --state-dir /data/WYC/signLanguage/.codex/tmux-workers --session signlanguage-scoring-workers job-add scoring-design --pid <PID> --name <job-name> --log <log-path> --command '<command>'
```

## Coordinator Notes

None.

## Required Completion Report

- Changed files, if any
- Commands run
- Result or metric evidence
- Blockers
- Next recommended action
