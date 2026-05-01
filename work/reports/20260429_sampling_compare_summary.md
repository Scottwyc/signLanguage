# 关键帧采样策略对比汇报

- 对象视频：`花.mp4`
- 采样预算：12
- 可视化形式：Holistic 叠加结果 + 关键点图 + 骨骼图
- 说明：本轮结果已修正中文标题遮挡问题，以下图表均为最新输出

## 目标

验证三种关键帧采样方式在同一视频样本上的表现差异，重点看两件事：

1. 是否能覆盖整段视频，而不是只看前半段
2. 在相同预算下，是否更贴近真实动作出现的时间分布

实现口径说明：

- `uniform` 直接按整段视频等间距选帧，最终 Holistic 识别先保存结果文件，再统一生成可视化
- `two_stage` 和 `adaptive` 在前半段会借助少量 Holistic 结果做采样决策，但最终采样完成时会同步保存最终 Holistic 结果文件，随后统一生成可视化，不再额外补跑一次识别
- 本报告只统计 `采样+Holistic` 总耗时，不再单列可视化计时

## 总体结论

三种方案都已经从“前段截断采样”升级为“全时长覆盖采样”，都能覆盖到视频末尾。

- `uniform`：最稳定，成本最低，适合作为默认基线
- `two_stage`：在保证全覆盖的前提下，开始向更值得关注的区间倾斜
- `adaptive`：对 `花.mp4` 这种动作开始偏晚的视频，最能把采样预算往后半段压缩，贴近动作出现位置，但采样耗时最高

如果只看当前这个视频样本的采样有效性，综合推荐顺序是：

1. `adaptive`
2. `two_stage`
3. `uniform`

说明：

- 这里的“效果好”主要指采样点是否覆盖整段视频、是否更贴近晚起始动作区间
- 表中的“平均运动能量”只是描述性参考，不直接等价于采样质量分数
- 耗时只看 `采样+Holistic` 的总成本，不再单独拆可视化
- `two_stage` 和 `adaptive` 在采样决策里已经包含前置 Holistic 过程，因此总成本更高

## 关键结果对比

| 策略 | 采样帧 | 帧覆盖比例 | 尾部覆盖比例 | 后半段采样占比 | 后 75% 采样占比 | 平均运动能量 | 采样+Holistic总耗时 |
|---|---:|---:|---:|---:|---:|---:|---:|
| uniform | `0, 10, 19, 29, 39, 48, 58, 67, 77, 87, 96, 106` | 1.0 | 1.0 | 0.50 | 0.25 | 6.4712 | 0.955s |
| two_stage | `0, 18, 26, 35, 44, 53, 62, 71, 79, 88, 97, 106` | 1.0 | 1.0 | 0.5833 | 0.25 | 3.7846 | 392.919s |
| adaptive | `0, 21, 42, 53, 58, 64, 69, 74, 79, 85, 95, 106` | 1.0 | 1.0 | 0.75 | 0.25 | 2.7614 | 652.791s |

## 视觉结果

### uniform

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/uniform/花/花_contact_sheet.png)

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/uniform/花/花_timeline.png)

要点：

- 采样位置最均匀，首尾都覆盖
- 对动作开始较晚的视频，前半段会保留更多“低信息密度”样本
- 适合作为稳定基线

### two_stage

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/two_stage/花/花_contact_sheet.png)

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/two_stage/花/花_timeline.png)

要点：

- 先全局粗扫，再往高价值区间补点
- 相比 `uniform`，后段样本更密，开始贴近动作展开区
- 在效果和计算成本之间更均衡

### adaptive

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/adaptive/花/花_contact_sheet.png)

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/adaptive/花/花_timeline.png)

要点：

- 后半段采样占比最高，最符合 `花.mp4` 这类“动作开始偏晚”的样本
- 采样分布更集中到真正有动作变化的区间
- 代价是采样阶段最慢

## 耗时观察

- `uniform` 最快，因为它只做均匀选帧，然后对 12 帧做一次最终 Holistic。
- `two_stage` 需要先做粗扫再补点，所以总耗时更高，但比 adaptive 更平衡。
- `adaptive` 采样决策最复杂，因此总耗时最高，但对晚起始动作最敏感。
- 这三种方法的差异，主要来自“采样决策过程”的复杂度，而不是最后的可视化。

## 结论

对 `花.mp4` 这个样本来说，最关键的变化不是“有没有采样”，而是“采样是否覆盖到了真正动作出现的后段”。

三种新方案都解决了原来前段截断的问题，但它们对后段动作的关注程度不同：

- `uniform` 解决覆盖问题，但关注度最平均
- `two_stage` 在覆盖和聚焦之间折中
- `adaptive` 最适合动作开始较晚、后段变化更集中的样本

如果后续要继续推进，建议把这三类采样都保留为可切换策略，再扩展到更多视频样本上做横向对比。
