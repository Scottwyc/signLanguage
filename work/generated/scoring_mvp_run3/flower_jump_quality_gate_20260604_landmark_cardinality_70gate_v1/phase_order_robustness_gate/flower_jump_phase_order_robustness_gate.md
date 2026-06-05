# 花/跳语义相位顺序鲁棒性门

- 生成时间：`2026-06-04T13:56:04`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架序列层面加入相位速度变形或错序假动作；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：单调相位快慢变化仍高分；倒放、前后错序、三相位乱序不能通过。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`26`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 单调变形最低分 | 最弱单调变形 | 错序最高分 | 最强错序变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 79.410 | ordered_jitter | 33.723 | scramble_three_phases |
| 跳 | PASS | 69.389 | ordered_jitter | 45.000 | swap_halves |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|
| reverse_full | negative | PASS | 14.024 | <= 50.0 或重采/语义失败 | 1.000 | semantic_mismatch | phase_order_disorder | 完整倒放，动作语义起终点和方向相反。 |
| swap_halves | negative | PASS | 28.941 | <= 50.0 或重采/语义失败 | 1.000 | semantic_mismatch | phase_order_disorder | 前后半段错序，语义相位不连续。 |
| scramble_three_phases | negative | PASS | 33.723 | <= 50.0 或重采/语义失败 | 1.000 | semantic_mismatch | phase_order_disorder | 结束、中段、开始三相位乱序。 |
| ordered_jitter | positive | PASS | 79.410 | >= 68.0 | 1.000 | score_valid | score_valid | 轻微采样抖动但整体相位顺序不变。 |
| fast_start_slow_end | positive | PASS | 93.082 | >= 70.0 | 1.000 | score_valid | score_valid | 动作相位单调但前段快、后段慢。 |
| ease_in_out | positive | PASS | 94.339 | >= 70.0 | 1.000 | score_valid | score_valid | 自然加速再减速，核心语义顺序不变。 |
| slow_start_fast_end | positive | PASS | 96.056 | >= 70.0 | 1.000 | score_valid | score_valid | 动作相位单调但前段慢、后段快。 |
| middle_hold_30pct | positive | PASS | 97.464 | >= 70.0 | 1.302 | score_valid | score_valid | 核心姿态附近短暂停留，但完整动作仍在。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|
| reverse_full | negative | PASS | 20.525 | <= 50.0 或重采/语义失败 | 1.000 | semantic_mismatch | phase_order_disorder | 完整倒放，动作语义起终点和方向相反。 |
| swap_halves | negative | PASS | 45.000 | <= 50.0 或重采/语义失败 | 1.000 | semantic_mismatch | phase_order_disorder | 前后半段错序，语义相位不连续。 |
| scramble_three_phases | negative | PASS | 45.000 | <= 50.0 或重采/语义失败 | 1.000 | semantic_mismatch | phase_order_disorder | 结束、中段、开始三相位乱序。 |
| ordered_jitter | positive | PASS | 69.389 | >= 68.0 | 1.000 | score_valid | score_valid | 轻微采样抖动但整体相位顺序不变。 |
| ease_in_out | positive | PASS | 77.248 | >= 70.0 | 1.000 | score_valid | score_valid | 自然加速再减速，核心语义顺序不变。 |
| fast_start_slow_end | positive | PASS | 79.524 | >= 70.0 | 1.000 | score_valid | score_valid | 动作相位单调但前段快、后段慢。 |
| middle_hold_30pct | positive | PASS | 93.738 | >= 70.0 | 1.316 | score_valid | score_valid | 核心姿态附近短暂停留，但完整动作仍在。 |
| slow_start_fast_end | positive | PASS | 96.618 | >= 70.0 | 1.000 | score_valid | score_valid | 动作相位单调但前段慢、后段快。 |

## 说明

- 正向相位变形验证不同用户动作速度曲线不一致时，DTW 仍能对齐核心语义顺序。
- 负向错序变体验证评分不是只看静态骨架集合，而是看动作语义的起点、中段和终点顺序。
- 该门是合成时序压力测试，不能替代真实网页摄像头样本。
