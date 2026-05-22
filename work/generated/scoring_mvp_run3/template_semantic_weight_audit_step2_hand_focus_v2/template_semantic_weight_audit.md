# 模板库语义权重与动态帧权重审计

- 生成时间：`2026-05-23T02:49:56`
- 模板根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 样本数：`10`
- 完全通过：`10`
- 需复核：`0`

## 总览

| 词条 | 帧数 | profile | 重要组 | 权重峰值 | 峰谷比 | 状态 | 问题 |
|---|---:|---|---|---:|---:|---|---|
| 唱歌 | 27 | 唱歌 | left_hand,right_hand,face,pose | 1.525 | 2.037 | ok | - |
| 指示 | 30 | 指示 | right_hand,right_hand_shape,left_hand | 1.504 | 1.827 | ok | - |
| 月亮 | 47 | 月亮 | left_hand_shape,right_hand_shape,left_hand,right_hand | 1.715 | 2.449 | ok | - |
| 朋友 | 28 | 朋友 | left_hand,right_hand,left_hand_shape,right_hand_shape | 1.367 | 1.914 | ok | - |
| 汽车 | 44 | 汽车 | left_hand,right_hand,left_hand_shape,right_hand_shape | 1.431 | 1.617 | ok | - |
| 花 | 53 | 花 | right_hand_shape,right_hand | 1.673 | 2.092 | ok | - |
| 虎 | 54 | 虎 | left_hand_shape,right_hand_shape,left_hand,right_hand | 1.719 | 2.176 | ok | - |
| 谗（羡慕） | 32 | 谗（羡慕） | face,right_hand,left_hand | 1.354 | 1.582 | ok | - |
| 跳 | 19 | 跳 | right_hand_shape,right_hand | 1.346 | 1.733 | ok | - |
| 香蕉 | 42 | 香蕉 | right_hand,left_hand,right_hand_shape,left_hand_shape | 1.705 | 2.053 | ok | - |

## 重要帧

### 唱歌

- rank 1: frame `4`, t=`0.160s`, weight=`1.525`
- rank 2: frame `6`, t=`0.240s`, weight=`1.368`
- rank 3: frame `2`, t=`0.080s`, weight=`1.307`
- rank 4: frame `32`, t=`1.280s`, weight=`1.175`
- rank 5: frame `30`, t=`1.200s`, weight=`1.147`
- rank 6: frame `24`, t=`0.960s`, weight=`1.120`

### 指示

- rank 1: frame `10`, t=`0.448s`, weight=`1.504`
- rank 2: frame `8`, t=`0.359s`, weight=`1.400`
- rank 3: frame `12`, t=`0.538s`, weight=`1.390`
- rank 4: frame `14`, t=`0.628s`, weight=`1.208`
- rank 5: frame `36`, t=`1.614s`, weight=`1.170`
- rank 6: frame `34`, t=`1.524s`, weight=`1.159`

### 月亮

- rank 1: frame `14`, t=`0.560s`, weight=`1.715`
- rank 2: frame `12`, t=`0.480s`, weight=`1.707`
- rank 3: frame `16`, t=`0.640s`, weight=`1.697`
- rank 4: frame `10`, t=`0.400s`, weight=`1.679`
- rank 5: frame `18`, t=`0.720s`, weight=`1.562`
- rank 6: frame `8`, t=`0.320s`, weight=`1.466`

### 朋友

- rank 1: frame `34`, t=`1.360s`, weight=`1.367`
- rank 2: frame `32`, t=`1.280s`, weight=`1.263`
- rank 3: frame `36`, t=`1.440s`, weight=`1.258`
- rank 4: frame `44`, t=`1.760s`, weight=`1.243`
- rank 5: frame `46`, t=`1.840s`, weight=`1.234`
- rank 6: frame `42`, t=`1.680s`, weight=`1.203`

### 汽车

- rank 1: frame `20`, t=`0.759s`, weight=`1.431`
- rank 2: frame `18`, t=`0.683s`, weight=`1.361`
- rank 3: frame `22`, t=`0.834s`, weight=`1.324`
- rank 4: frame `32`, t=`1.214s`, weight=`1.290`
- rank 5: frame `34`, t=`1.290s`, weight=`1.238`
- rank 6: frame `30`, t=`1.138s`, weight=`1.210`

### 花

- rank 1: frame `38`, t=`1.290s`, weight=`1.673`
- rank 2: frame `48`, t=`1.630s`, weight=`1.588`
- rank 3: frame `40`, t=`1.358s`, weight=`1.586`
- rank 4: frame `46`, t=`1.562s`, weight=`1.567`
- rank 5: frame `36`, t=`1.222s`, weight=`1.545`
- rank 6: frame `50`, t=`1.698s`, weight=`1.483`

### 虎

- rank 1: frame `64`, t=`2.269s`, weight=`1.719`
- rank 2: frame `62`, t=`2.198s`, weight=`1.719`
- rank 3: frame `66`, t=`2.340s`, weight=`1.619`
- rank 4: frame `60`, t=`2.127s`, weight=`1.578`
- rank 5: frame `68`, t=`2.411s`, weight=`1.352`
- rank 6: frame `70`, t=`2.482s`, weight=`1.232`

### 谗（羡慕）

- rank 1: frame `46`, t=`1.731s`, weight=`1.354`
- rank 2: frame `50`, t=`1.882s`, weight=`1.337`
- rank 3: frame `48`, t=`1.806s`, weight=`1.326`
- rank 4: frame `44`, t=`1.656s`, weight=`1.296`
- rank 5: frame `52`, t=`1.957s`, weight=`1.246`
- rank 6: frame `14`, t=`0.527s`, weight=`1.225`

### 跳

- rank 1: frame `16`, t=`1.090s`, weight=`1.346`
- rank 2: frame `6`, t=`0.409s`, weight=`1.317`
- rank 3: frame `14`, t=`0.954s`, weight=`1.288`
- rank 4: frame `8`, t=`0.545s`, weight=`1.253`
- rank 5: frame `18`, t=`1.226s`, weight=`1.201`
- rank 6: frame `4`, t=`0.272s`, weight=`1.116`

### 香蕉

- rank 1: frame `12`, t=`0.468s`, weight=`1.705`
- rank 2: frame `14`, t=`0.546s`, weight=`1.660`
- rank 3: frame `10`, t=`0.390s`, weight=`1.617`
- rank 4: frame `16`, t=`0.624s`, weight=`1.392`
- rank 5: frame `8`, t=`0.312s`, weight=`1.213`
- rank 6: frame `42`, t=`1.639s`, weight=`1.183`

## 说明

- `semantic_frame_weights.json` 已写回每个模板目录，作为数据库侧的逐帧动态权重 manifest。
- 评分时仍会根据当前语义 profile 重新计算动态权重；若目录中存在 manifest，会作为数据库侧先验加载，并与实时动态权重归一化合并。
- `review` 不等于失败，表示帧数过低、重要组检出率低或动态峰值不明显，需要后续补采或人工复核。
