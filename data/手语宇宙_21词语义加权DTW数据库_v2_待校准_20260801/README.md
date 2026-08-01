# 手语宇宙 21 词语义加权 DTW 数据库 v2

最后更新：2026-08-01 15:50 +0800

## 状态

- 数据库状态：`provisional_pending_manual_cutpoint_and_weight_calibration`
- 词汇数：21
- 样本数：1,384
- 特征帧数：45,310
- 加权分片数：1,384
- 自动结构校验错误：0
- 体积：约 56 MB

本数据库是原始 Landmark 数据库的派生层，不复制完整 Landmark，只保存面向 DTW 的归一化局部特征、mask 和权重。

## 数据来源

- 原始数据库：`/data/WYC/signLanguage/data/手语宇宙_原始Holistic_Landmark数据库_v2中文兼容格式_待人工审核_20260801`
- 最新语义资料：`/data/WYC/signLanguage/data/Demo词汇(21个）.docx`
- 语义 Profile：`/data/WYC/signLanguage/work/generated/demo21_semantic_profiles_20260801/demo21_semantic_weights_v2.json`

## 词序

数据库同时保留两套顺序：

1. `acquisition_word_index`：A-Z 长视频采集节点顺序，用于切割标签。
2. `document_order`：最新 DOCX 的展示/语义组织顺序。

不能用 DOCX 顺序直接重标视频节点。

## 汽车变体

- `汽车（一）`：`汽车_方向盘`，双手虚握方向盘并左右转动。
- `汽车二`：`汽车_车身前行`，单手形成车身并向前移动。

该映射已由用户确认，并通过多个视频片段尾部密集帧复核。

## 每帧特征维数

- Pose：27（9 个核心点 × xyz）
- 左手位置：63（21 × xyz）
- 右手位置：63（21 × xyz）
- Face：36（12 个核心点 × xyz）
- 左手手形：19
- 右手手形：19
- 双手关系：8

所有组使用固定维数。Landmark 缺失时写零向量并将 mask 置零，避免把缺失误当成真实零坐标。

## 语义权重

每个词单独保存：

- `group_weights`
- `keypoint_weights`
- `focus_groups`
- `semantic_dtw`
- `semantic_phases`
- `semantic_notes`

旧 10 词沿用历史 Profile；其余词根据最新 DOCX 建立工程权重。新增 Profile 尚未经过正负样本经验校准，不能直接宣称为最终评分标准。

## 目录结构

```text
features/
└── 01_谗（羡慕）/
    └── 用户_01/
        └── 正/
            ├── 重复_01.json.gz
            └── 重复_02.json.gz
```

派生特征采用压缩 JSON，主索引和 Profile 是普通 JSON。每个派生分片包含 `raw_landmark_shard`，可追溯到原始普通 JSON。

## 主要文件

- `weighted_database.json`：以词汇为顶层键的加权数据库
- `weighted_sample_manifest.csv`：样本与原始/派生分片映射
- `validation_summary.json`：全量验证结果

## 后续校准

1. 完成人工切割审核后重建受影响样本。
2. 构建同词正样本、异词负样本和错误动作样本。
3. 对新 11 词校准 group/keypoint/phase 权重。
4. 验证主辅手镜像策略、视角一致性和跨用户泛化。
5. 固定经过验证的权重版本，再用于正式评分。
