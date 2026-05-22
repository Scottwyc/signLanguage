# 模板库语义权重与动态帧权重审计

- 生成时间：`2026-05-23T01:23:30`
- 模板根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 样本数：`10`
- 完全通过：`8`
- 需复核：`2`

## 总览

| 词条 | 帧数 | profile | 重要组 | 权重峰值 | 峰谷比 | 状态 | 问题 |
|---|---:|---|---|---:|---:|---|---|
| 唱歌 | 14 | 唱歌 | left_hand,right_hand,face,pose | 1.245 | 1.665 | ok | - |
| 指示 | 16 | 指示 | right_hand,right_hand_shape,left_hand | 1.498 | 2.068 | ok | - |
| 月亮 | 24 | 月亮 | left_hand_shape,right_hand_shape,left_hand,right_hand | 1.588 | 2.300 | ok | - |
| 朋友 | 15 | 朋友 | left_hand,right_hand,left_hand_shape,right_hand_shape | 1.322 | 1.860 | ok | - |
| 汽车 | 23 | 汽车 | left_hand,right_hand,left_hand_shape,right_hand_shape | 1.346 | 1.815 | ok | - |
| 花 | 28 | 花 | right_hand_shape,left_hand_shape,right_hand,left_hand | 1.389 | 1.642 | review | low_focus_presence:left_hand_shape, low_focus_presence:left_hand |
| 虎 | 29 | 虎 | left_hand_shape,right_hand_shape,left_hand,right_hand | 1.422 | 2.072 | ok | - |
| 谗（羡慕） | 17 | 谗（羡慕） | face,right_hand,left_hand | 1.397 | 1.749 | ok | - |
| 跳 | 10 | 跳 | right_hand_shape,right_hand,left_hand | 1.377 | 1.800 | review | low_template_frame_count |
| 香蕉 | 22 | 香蕉 | right_hand,left_hand,right_hand_shape,left_hand_shape | 1.638 | 2.202 | ok | - |

## 重要帧

### 唱歌

- rank 1: frame `28`, t=`1.120s`, weight=`1.245`
- rank 2: frame `24`, t=`0.960s`, weight=`1.222`
- rank 3: frame `8`, t=`0.320s`, weight=`1.218`
- rank 4: frame `4`, t=`0.160s`, weight=`1.165`
- rank 5: frame `32`, t=`1.280s`, weight=`1.107`
- rank 6: frame `20`, t=`0.800s`, weight=`1.097`

### 指示

- rank 1: frame `12`, t=`0.538s`, weight=`1.498`
- rank 2: frame `16`, t=`0.717s`, weight=`1.401`
- rank 3: frame `8`, t=`0.359s`, weight=`1.288`
- rank 4: frame `20`, t=`0.897s`, weight=`1.267`
- rank 5: frame `24`, t=`1.076s`, weight=`1.184`
- rank 6: frame `32`, t=`1.435s`, weight=`1.174`

### 月亮

- rank 1: frame `12`, t=`0.480s`, weight=`1.588`
- rank 2: frame `16`, t=`0.640s`, weight=`1.556`
- rank 3: frame `20`, t=`0.800s`, weight=`1.361`
- rank 4: frame `8`, t=`0.320s`, weight=`1.355`
- rank 5: frame `80`, t=`3.200s`, weight=`1.220`
- rank 6: frame `84`, t=`3.360s`, weight=`1.218`

### 朋友

- rank 1: frame `12`, t=`0.480s`, weight=`1.322`
- rank 2: frame `8`, t=`0.320s`, weight=`1.289`
- rank 3: frame `16`, t=`0.640s`, weight=`1.194`
- rank 4: frame `20`, t=`0.800s`, weight=`1.062`
- rank 5: frame `4`, t=`0.160s`, weight=`1.015`
- rank 6: frame `24`, t=`0.960s`, weight=`0.998`

### 汽车

- rank 1: frame `20`, t=`0.759s`, weight=`1.346`
- rank 2: frame `24`, t=`0.910s`, weight=`1.259`
- rank 3: frame `16`, t=`0.607s`, weight=`1.259`
- rank 4: frame `28`, t=`1.062s`, weight=`1.217`
- rank 5: frame `32`, t=`1.214s`, weight=`1.215`
- rank 6: frame `36`, t=`1.366s`, weight=`1.104`

### 花

- rank 1: frame `36`, t=`1.222s`, weight=`1.389`
- rank 2: frame `40`, t=`1.358s`, weight=`1.327`
- rank 3: frame `32`, t=`1.087s`, weight=`1.323`
- rank 4: frame `56`, t=`1.902s`, weight=`1.259`
- rank 5: frame `44`, t=`1.494s`, weight=`1.210`
- rank 6: frame `52`, t=`1.766s`, weight=`1.182`

### 虎

- rank 1: frame `64`, t=`2.269s`, weight=`1.422`
- rank 2: frame `68`, t=`2.411s`, weight=`1.421`
- rank 3: frame `72`, t=`2.553s`, weight=`1.361`
- rank 4: frame `60`, t=`2.127s`, weight=`1.307`
- rank 5: frame `76`, t=`2.695s`, weight=`1.279`
- rank 6: frame `104`, t=`3.687s`, weight=`1.166`

### 谗（羡慕）

- rank 1: frame `12`, t=`0.452s`, weight=`1.397`
- rank 2: frame `16`, t=`0.602s`, weight=`1.362`
- rank 3: frame `48`, t=`1.806s`, weight=`1.319`
- rank 4: frame `44`, t=`1.656s`, weight=`1.206`
- rank 5: frame `52`, t=`1.957s`, weight=`1.158`
- rank 6: frame `20`, t=`0.753s`, weight=`1.127`

### 跳

- rank 1: frame `12`, t=`0.817s`, weight=`1.377`
- rank 2: frame `16`, t=`1.090s`, weight=`1.352`
- rank 3: frame `8`, t=`0.545s`, weight=`1.159`
- rank 4: frame `20`, t=`1.362s`, weight=`1.090`
- rank 5: frame `32`, t=`2.179s`, weight=`0.868`
- rank 6: frame `4`, t=`0.272s`, weight=`0.862`

### 香蕉

- rank 1: frame `16`, t=`0.624s`, weight=`1.638`
- rank 2: frame `12`, t=`0.468s`, weight=`1.601`
- rank 3: frame `20`, t=`0.780s`, weight=`1.481`
- rank 4: frame `24`, t=`0.937s`, weight=`1.378`
- rank 5: frame `28`, t=`1.093s`, weight=`1.244`
- rank 6: frame `8`, t=`0.312s`, weight=`1.211`

## 说明

- `semantic_frame_weights.json` 已写回每个模板目录，作为数据库侧的逐帧动态权重 manifest。
- 评分时仍会根据当前语义 profile 重新计算动态权重；若目录中存在 manifest，会作为数据库侧先验加载，并与实时动态权重归一化合并。
- `review` 不等于失败，表示帧数过低、重要组检出率低或动态峰值不明显，需要后续补采或人工复核。
