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
