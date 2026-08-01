# 手语宇宙原始 Holistic Landmark 数据库 v2

最后更新：2026-08-01 15:50 +0800

## 状态

- 数据库状态：`provisional_pending_manual_cutpoint_review`
- 词汇数：21
- 样本数：1,384
- Landmark 帧数：45,310
- 自动结构校验错误：0
- 未生成样本：2，均为编号 11 左30°源视频尾部截断导致缺失的“指示”两次。
- 本数据库包含私有生物运动信息，不允许直接公开发布。

## 目录结构

```text
landmarks/
└── 01_谗（羡慕）/
    └── 用户_01/
        └── 正/
            ├── 重复_01.json
            └── 重复_02.json
```

顶层索引 `word_database.json` 采用：

```text
标准词汇 → 用户编号 → 视角 → 重复次数 → Landmark JSON
```

## 单样本格式

普通 JSON 可直接用 VS Code、`less` 或 Python 查看。坐标结构兼容历史 Holistic worker：

```text
records[].result_data.pose_landmarks
records[].result_data.left_hand_landmarks
records[].result_data.right_hand_landmarks
records[].result_data.face_landmarks
```

每个点为 `{x,y,z,...}` 对象。Pose 额外保存 `visibility/presence`。

Landmark Schema：

- Pose：33 点
- 左手：21 点
- 右手：21 点
- Face：12 个核心眼口点
- Face 原始 MediaPipe ID：`[33,133,159,145,362,263,386,374,61,291,13,14]`

## 采样参数

- 请求采样率：12 FPS
- 最大处理宽度：640
- 后端：5 个常驻 Holistic Worker
- 原始像素：不入库
- 切割时间点：Holistic 静止姿态微调候选，仍待人工完整审核

## 质量统计

- 请求帧：45,355
- 成功 Landmark 帧：45,310
- 无法恢复帧：45
- 缺帧率：0.0992%
- Pose 有效帧：45,310
- 左手有效帧：42,140
- 右手有效帧：41,415
- Face 有效帧：45,201

完整验证：`validation_summary.json`

## 主要文件

- `database_index.json`：带数据库元数据和缺失项的完整索引
- `word_database.json`：以标准词汇为顶层键的纯键值数据库
- `sample_manifest.csv`：1,384 个样本的扁平清单
- `private_provenance_manifest.json`：私有源视频路径与哈希
- `validation_summary.json`：全量结构验证结果

## 人工审核后的更新方式

人工修改切割边界后，应只重建对应编号/视角的视频分片，并更新：

1. `sample_manifest.csv`
2. `database_index.json`
3. `word_database.json`
4. `private_provenance_manifest.json` 中的切割 CSV 哈希
5. 下游加权 DTW 派生分片

不得直接手工修改 Landmark 坐标。
