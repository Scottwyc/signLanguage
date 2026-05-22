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
