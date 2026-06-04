# Browser Upload Weight Simulation Gate

- generated_at: `2026-06-04T01:56:26`
- status: **PASS**
- app_js: `/data/WYC/signLanguage/work/web/static/app.js`
- node_returncode: `0`

## Cases

| case | word | status | selected/target | candidate | weight range | unique | top selected | endpoints |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `flower_opening_motion` | `花` | `PASS` | 13/13 | 25 | 1.2505 | 11 | 6 | True/True |
| `jump_burst_motion` | `跳` | `PASS` | 10/10 | 20 | 1.9795 | 8 | 6 | True/True |
| `static_hold` | `花` | `PASS` | 13/13 | 25 | 0.0000 | 1 | 6 | True/True |

## Checks

| case | check | result | detail |
| --- | --- | --- | --- |
| `flower_opening_motion` | `selected_count_matches_target` | `PASS` | selected=13 target=13 |
| `flower_opening_motion` | `target_frames_meet_recommendation` | `PASS` | target=13 min=12 |
| `flower_opening_motion` | `candidate_pool_is_denser_than_upload` | `PASS` | candidate=25 target=13 |
| `flower_opening_motion` | `frame_indices_strictly_in_order` | `PASS` | indices=[0, 3, 6, 7, 8, 9, 12, 15, 17, 18, 19, 21, 24] |
| `flower_opening_motion` | `coverage_keeps_start_and_end` | `PASS` | first=True last=True |
| `flower_opening_motion` | `motion_weights_are_nonuniform` | `PASS` | range=1.2505, min=0.4274, max=1.6779 |
| `flower_opening_motion` | `motion_weight_has_multiple_levels` | `PASS` | unique_4dp=11 |
| `flower_opening_motion` | `motion_peaks_are_selected` | `PASS` | selected_top_energy_count=6 top_energy_indices=[18, 17, 7, 8, 19, 9] |
| `jump_burst_motion` | `selected_count_matches_target` | `PASS` | selected=10 target=10 |
| `jump_burst_motion` | `target_frames_meet_recommendation` | `PASS` | target=10 min=6 |
| `jump_burst_motion` | `candidate_pool_is_denser_than_upload` | `PASS` | candidate=20 target=10 |
| `jump_burst_motion` | `frame_indices_strictly_in_order` | `PASS` | indices=[0, 4, 8, 9, 10, 11, 12, 13, 15, 19] |
| `jump_burst_motion` | `coverage_keeps_start_and_end` | `PASS` | first=True last=True |
| `jump_burst_motion` | `motion_weights_are_nonuniform` | `PASS` | range=1.9794999999999998, min=0.4114, max=2.3909 |
| `jump_burst_motion` | `motion_weight_has_multiple_levels` | `PASS` | unique_4dp=8 |
| `jump_burst_motion` | `motion_peaks_are_selected` | `PASS` | selected_top_energy_count=6 top_energy_indices=[11, 12, 10, 8, 9, 13] |
| `static_hold` | `selected_count_matches_target` | `PASS` | selected=13 target=13 |
| `static_hold` | `target_frames_meet_recommendation` | `PASS` | target=13 min=12 |
| `static_hold` | `candidate_pool_is_denser_than_upload` | `PASS` | candidate=25 target=13 |
| `static_hold` | `frame_indices_strictly_in_order` | `PASS` | indices=[0, 1, 2, 3, 4, 5, 6, 9, 12, 15, 18, 21, 24] |
| `static_hold` | `coverage_keeps_start_and_end` | `PASS` | first=True last=True |
| `static_hold` | `static_weights_remain_uniform` | `PASS` | range=0 |
| `static_hold` | `static_not_completion_strong_frame_weight_evidence` | `PASS` | nonuniform=False |
