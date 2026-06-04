# Browser Upload Weight Simulation Gate

- generated_at: `2026-06-03T08:47:50`
- status: **FAIL**
- app_js: `/data/WYC/signLanguage/work/web/static/app.js`
- node_returncode: `0`

## Cases

| case | word | status | selected/target | candidate | weight range | unique | top selected | endpoints |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

## Checks

| case | check | result | detail |
| --- | --- | --- | --- |

## Node Stderr

```

JSON parse failed: Expecting value: line 1 column 1 (char 0)
```

## Node Stdout

```
Node.js EventListener MaxListeners 已设置为 100
{
  "cases": [
    {
      "name": "flower_opening_motion",
      "word": "花",
      "plan": {
        "word": "花",
        "durationSec": 2.5,
        "uploadFps": 5,
        "targetFrames": 13,
        "candidateFps": 10,
        "candidateFrames": 25,
        "minFrames": 12
      },
      "selected_count": 13,
      "frame_indices": [
        0,
        5,
        6,
        7,
        8,
        9,
        10,
        14,
        16,
        17,
        18,
        19,
        24
      ],
      "frame_weights": [
        0.4274,
        0.9694,
        1.3859,
        1.5183,
        1.4951,
        1.4461,
        1.3647,
        1.1355,
        1.3739,
        1.5563,
        1.6779,
        1.4639,
        0.4274
      ],
      "weights_min": 0.4274,
      "weights_max": 1.6779,
      "weights_range": 1.2505,
      "weights_unique_4dp": 12,
      "top_energy_indices": [
        18,
        17,
        7,
        8,
        19,
        9
      ],
      "selected_top_energy_count": 6,
      "selected_in_order": true,
      "includes_first_frame": true,
      "includes_last_frame": true,
      "nonuniform_weights": true
    },
    {
      "name": "jump_burst_motion",
      "word": "跳",
      "plan": {
        "word": "跳",
        "durationSec": 2,
        "uploadFps": 5,
        "targetFrames": 10,
        "candidateFps": 10,
        "candidateFrames": 20,
        "minFrames": 6
      },
      "selected_count": 10,
      "frame_indices": [
        0,
        5,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        19
      ],
      "frame_weights": [
        0.4114,
        0.4114,
        1.6608,
        1.5993,
        1.7996,
        2.3909,
        2.1297,
        1.455,
        1.3236,
        0.4114
      ],
      "weights_min": 0.4114,
      "weights_max": 2.3909,
      "weights_range": 1.9794999999999998,
      "weights_unique_4dp": 8,
      "top_energy_indices": [
        11,
        12,
        10,
        8,
        9,
        13
      ],
      "selected_top_energy_count": 6,
      "selected_in_order": true,
      "includes_first_frame": true,
      "includes_last_frame": true,
      "nonuniform_weights": true
    },
    {
      "name": "static_hold",
      "word": "花",
      "plan": {
        "word": "花",
        "durationSec": 2.5,
        "uploadFps": 5,
        "targetFrames": 13,
        "candidateFps": 10,
        "candidateFrames": 25,
        "minFrames": 12
      },
      "selected_count": 13,
      "frame_indices": [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        10,
        14,
        19,
        24
      ],
      "frame_weights": [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1
      ],
      "weights_min": 1,
      "weights_max": 1,
      "weights_range": 0,
      "weights_unique_4dp": 1,
      "top_energy_indices": [
        0,
        1,
        2,
        3,
        4,
        5
      ],
      "selected_top_energy_count": 6,
      "selected_in_order": true,
      "includes_first_frame": true,
      "includes_last_frame": true,
      "nonuniform_weights": false
    }
  ]
}

```
