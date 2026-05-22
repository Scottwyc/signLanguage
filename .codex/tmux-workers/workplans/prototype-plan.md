# Codex Tmux Worker Plan - prototype-plan

Created: 2026-05-20T17:16:30+08:00
Session: signlanguage-scoring-workers
Window: cw-prototype-plan
Working directory: /data/WYC/signLanguage
Model: gpt-5.5
Reasoning effort: xhigh

## Task

You are Worker prototype-plan in a tmux-launched Codex process.

Goal: inspect existing scripts and propose a minimal scoring prototype implementation plan that fits the current codebase.

Working directory: /data/WYC/signLanguage

Write scope:
- Write only /data/WYC/signLanguage/work/reports/scoring_mvp_prototype_plan_20260520_draft.md
- You may update your assigned progress/report files under /data/WYC/signLanguage/.codex/tmux-workers/

Do not modify:
- Source scripts
- Existing worklogs
- Existing generated artifacts
- Other scoring report drafts

Use these constraints:
- No real user samples are available; propose offline sanity checks using demo videos, pseudo-user perturbations, and different-word negatives.
- Prefer reusing existing code under /data/WYC/signLanguage/work/scripts.
- The prototype should read cached Holistic JSON and avoid rerunning Holistic unless a cache is missing.
- Use /home/wuyangcheng/myenv for Python execution if you run lightweight inspections.

Tasks:
1. Inspect existing scripts and identify reusable functions/modules for reading Holistic rows, keyframe selection, metrics, and visualization.
2. Propose a minimal script/module layout for the scoring prototype.
3. Define output JSON structure and visualization/report artifacts.
4. Define sanity-check cases and expected qualitative behavior.
5. Note implementation risks and any dependency gaps.
6. Write a Chinese draft report to your owned path.

Return: changed files, commands run, key findings, blockers, and next recommendation.

## Write Scope

- report:/data/WYC/signLanguage/work/reports/scoring_mvp_prototype_plan_20260520_draft.md

## Owned Paths

- /data/WYC/signLanguage/work/reports/scoring_mvp_prototype_plan_20260520_draft.md

## Resources

- cpu:prototype-plan

## Git Isolation

- Shared working tree.

## Inbox

/data/WYC/signLanguage/.codex/tmux-workers/inbox/prototype-plan

## Background Job Registry

/data/WYC/signLanguage/.codex/tmux-workers/jobs/prototype-plan.json

Register background jobs with:

```bash
python /home/wuyangcheng/.codex/skills/general/tmux-codex-parallel-workers/scripts/codex_tmux_manager.py --state-dir /data/WYC/signLanguage/.codex/tmux-workers --session signlanguage-scoring-workers job-add prototype-plan --pid <PID> --name <job-name> --log <log-path> --command '<command>'
```

## Coordinator Notes

None.

## Required Completion Report

- Changed files, if any
- Commands run
- Result or metric evidence
- Blockers
- Next recommended action
