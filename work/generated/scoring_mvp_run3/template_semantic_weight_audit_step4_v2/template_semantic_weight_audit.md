# 模板库语义权重与动态帧权重审计

- 生成时间：`2026-05-23T01:24:07`
- 模板根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 样本数：`10`
- 完全通过：`9`
- 需复核：`1`

## 总览

| 词条 | 帧数 | profile | 重要组 | 权重峰值 | 峰谷比 | 状态 | 问题 |
|---|---:|---|---|---:|---:|---|---|
| 唱歌 | 14 | 唱歌 | left_hand,right_hand,face,pose | 1.373 | 2.149 | ok | - |
| 指示 | 16 | 指示 | right_hand,right_hand_shape,left_hand | 1.784 | 2.975 | ok | - |
| 月亮 | 24 | 月亮 | left_hand_shape,right_hand_shape,left_hand,right_hand | 1.944 | 3.489 | ok | - |
| 朋友 | 15 | 朋友 | left_hand,right_hand,left_hand_shape,right_hand_shape | 1.505 | 2.537 | ok | - |
| 汽车 | 23 | 汽车 | left_hand,right_hand,left_hand_shape,right_hand_shape | 1.544 | 2.445 | ok | - |
| 花 | 28 | 花 | right_hand_shape,right_hand | 1.736 | 2.639 | ok | - |
| 虎 | 29 | 虎 | left_hand_shape,right_hand_shape,left_hand,right_hand | 1.665 | 2.982 | ok | - |
| 谗（羡慕） | 17 | 谗（羡慕） | face,right_hand,left_hand | 1.623 | 2.314 | ok | - |
| 跳 | 10 | 跳 | right_hand_shape,right_hand,left_hand | 1.589 | 2.415 | review | low_template_frame_count |
| 香蕉 | 22 | 香蕉 | right_hand,left_hand,right_hand_shape,left_hand_shape | 2.033 | 3.267 | ok | - |

## 重要帧

### 唱歌

- rank 1: frame `28`, t=`1.120s`, weight=`1.373`
- rank 2: frame `24`, t=`0.960s`, weight=`1.335`
- rank 3: frame `8`, t=`0.320s`, weight=`1.329`
- rank 4: frame `4`, t=`0.160s`, weight=`1.242`
- rank 5: frame `32`, t=`1.280s`, weight=`1.151`
- rank 6: frame `20`, t=`0.800s`, weight=`1.135`

### 指示

- rank 1: frame `12`, t=`0.538s`, weight=`1.784`
- rank 2: frame `16`, t=`0.717s`, weight=`1.614`
- rank 3: frame `8`, t=`0.359s`, weight=`1.423`
- rank 4: frame `20`, t=`0.897s`, weight=`1.387`
- rank 5: frame `24`, t=`1.076s`, weight=`1.254`
- rank 6: frame `32`, t=`1.435s`, weight=`1.238`

### 月亮

- rank 1: frame `12`, t=`0.480s`, weight=`1.944`
- rank 2: frame `16`, t=`0.640s`, weight=`1.886`
- rank 3: frame `20`, t=`0.800s`, weight=`1.542`
- rank 4: frame `8`, t=`0.320s`, weight=`1.533`
- rank 5: frame `80`, t=`3.200s`, weight=`1.310`
- rank 6: frame `84`, t=`3.360s`, weight=`1.306`

### 朋友

- rank 1: frame `12`, t=`0.480s`, weight=`1.505`
- rank 2: frame `8`, t=`0.320s`, weight=`1.449`
- rank 3: frame `16`, t=`0.640s`, weight=`1.293`
- rank 4: frame `20`, t=`0.800s`, weight=`1.085`
- rank 5: frame `4`, t=`0.160s`, weight=`1.013`
- rank 6: frame `24`, t=`0.960s`, weight=`0.988`

### 汽车

- rank 1: frame `20`, t=`0.759s`, weight=`1.544`
- rank 2: frame `24`, t=`0.910s`, weight=`1.398`
- rank 3: frame `16`, t=`0.607s`, weight=`1.397`
- rank 4: frame `28`, t=`1.062s`, weight=`1.328`
- rank 5: frame `32`, t=`1.214s`, weight=`1.325`
- rank 6: frame `36`, t=`1.366s`, weight=`1.147`

### 花

- rank 1: frame `36`, t=`1.222s`, weight=`1.736`
- rank 2: frame `40`, t=`1.358s`, weight=`1.633`
- rank 3: frame `32`, t=`1.087s`, weight=`1.584`
- rank 4: frame `56`, t=`1.902s`, weight=`1.508`
- rank 5: frame `44`, t=`1.494s`, weight=`1.410`
- rank 6: frame `52`, t=`1.766s`, weight=`1.361`

### 虎

- rank 1: frame `64`, t=`2.269s`, weight=`1.665`
- rank 2: frame `68`, t=`2.411s`, weight=`1.664`
- rank 3: frame `72`, t=`2.553s`, weight=`1.558`
- rank 4: frame `60`, t=`2.127s`, weight=`1.467`
- rank 5: frame `76`, t=`2.695s`, weight=`1.420`
- rank 6: frame `104`, t=`3.687s`, weight=`1.236`

### 谗（羡慕）

- rank 1: frame `12`, t=`0.452s`, weight=`1.623`
- rank 2: frame `16`, t=`0.602s`, weight=`1.562`
- rank 3: frame `48`, t=`1.806s`, weight=`1.488`
- rank 4: frame `44`, t=`1.656s`, weight=`1.302`
- rank 5: frame `52`, t=`1.957s`, weight=`1.224`
- rank 6: frame `20`, t=`0.753s`, weight=`1.176`

### 跳

- rank 1: frame `12`, t=`0.817s`, weight=`1.589`
- rank 2: frame `16`, t=`1.090s`, weight=`1.546`
- rank 3: frame `8`, t=`0.545s`, weight=`1.227`
- rank 4: frame `20`, t=`1.362s`, weight=`1.119`
- rank 5: frame `32`, t=`2.179s`, weight=`0.795`
- rank 6: frame `4`, t=`0.272s`, weight=`0.787`

### 香蕉

- rank 1: frame `16`, t=`0.624s`, weight=`2.033`
- rank 2: frame `12`, t=`0.468s`, weight=`1.964`
- rank 3: frame `20`, t=`0.780s`, weight=`1.747`
- rank 4: frame `24`, t=`0.937s`, weight=`1.569`
- rank 5: frame `28`, t=`1.093s`, weight=`1.346`
- rank 6: frame `8`, t=`0.312s`, weight=`1.293`

## 说明

- `semantic_frame_weights.json` 已写回每个模板目录，作为数据库侧的逐帧动态权重 manifest。
- 评分时仍会根据当前语义 profile 重新计算动态权重；若目录中存在 manifest，会作为数据库侧先验加载，并与实时动态权重归一化合并。
- `review` 不等于失败，表示帧数过低、重要组检出率低或动态峰值不明显，需要后续补采或人工复核。
