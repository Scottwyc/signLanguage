# 花/跳浏览器采集证据门

- generated_at: `2026-06-03T11:38:55`
- status: **PASS**
- fixture_root: `work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_v1/browser_evidence_gate/fixtures`
- watch_status_json: `work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_v1/browser_evidence_gate/fixtures/watch_status.json`
- 口径：只复制保存样本到隔离目录并修改 metadata；不调用 `/api/score`，不运行 Holistic，不移动 marker。

| case | result | ready | evidence | levels | reasons |
|---|---|---:|---:|---|---|
| `legacy_frame_slice_only` | `PASS` | `False` | `False` | `legacy_frame_slice_metadata` | `legacy_frame_slice_metadata_not_completion_evidence` |
| `strong_nonuniform_frame_weights` | `PASS` | `True` | `True` | `strong_nonuniform_frame_weights` | `strong_nonuniform_frame_weights` |
| `uniform_frame_weights` | `PASS` | `False` | `False` | `none` | `source_metadata_missing` |
| `strong_client_source` | `PASS` | `True` | `True` | `strong_client_source` | `strong_client_source` |

## 结论

- 严格浏览器证据门通过：非均匀 frame_weights / browser client_source 可关闭证据门，legacy 或均匀权重不会误关。
