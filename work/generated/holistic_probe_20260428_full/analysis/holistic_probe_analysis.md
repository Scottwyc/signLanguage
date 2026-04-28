# Holistic 结果分析

- 生成时间：2026-04-28T19:52:53
- 视频数量：10
- 输出目录：/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/analysis

## 总体统计

- pose 平均覆盖率：1.0
- left hand 平均覆盖率：0.6383333333333333
- right hand 平均覆盖率：0.7066666666666667
- face 平均覆盖率：1.0
- 平均运动能量：27.710437961816787

## 结论

- pose 和 face 在这批 demo 中覆盖率稳定，说明人体主干和脸部动作特征对当前数据集比较容易被稳定捕获。
- 双手覆盖率存在明显差异，左手更容易掉帧或缺失，说明这批样本里存在单手主导、遮挡或画面构图偏置。
- 运动能量最高的视频通常对应动作幅度更明显、时序变化更强的词条，适合进一步做 DTW 或关键帧选择。

## 典型样本

- 左手覆盖最低：花.mp4 (0.0)
- 右手覆盖最低：花.mp4 (0.4166666666666667)
- 运动能量最高：唱歌.mp4 (78.82595189412434)

## 产物

- 覆盖率图：`/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/analysis/holistic_coverage_by_video.png`
- 运动能量图：`/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/analysis/holistic_motion_by_video.png`
