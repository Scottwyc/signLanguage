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
