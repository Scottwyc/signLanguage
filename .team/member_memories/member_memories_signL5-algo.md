# 成员工作记忆：signL5-algo（算法开发）

> 维护规范：跨 CLI 共享事实写 .team/ 共享文件（§4）；本文件记录 signL5-algo 个人工作上下文，主管可读。更新：2026-08-29（顾问更新 GPU 约束，内容仍为 8/11 主线待算法续写）

## 当前主线：坐姿裁剪数据增强（v6.4 完成）

### 数据
- 坐姿增强样本：/data/WYC/signLanguage/work/generated/sit_samples_v1_20260810/（13950 个：正样本坐姿化 2790 + 负例坐姿化 11160，S1/S2/S3 三级，errors=0）
- 特征：sit_features_v1.npz（13950×30×235）
- 遮挡模式对齐实测：髋/膝/踝 visibility→0 + 坐标漂移出画幅；肘/腕部分帧低可见；手形特征 MAE=0.00001（语义保持）

### 模型
- **v6.4 坐姿增强树模型**（zhuhai A30 单卡 0 训练，early stop ep95，best_leaf_avg=0.0431，站姿语义未退化）
- 权重：/data/WYC/signLanguage/work/generated/slu_model_runs_v2/sit_tree_v1/best_model.pt
- 对比基准 v6.3：/data/WYC/signLanguage/work/generated/slu_model_runs_v2/tree_v63_best_model.pt

### 关键结论（2026-08-11 目标叶子评估修正）
- 坐姿分级 S1/S2/S3 **有清晰梯度**（pos 坐姿化 0.8355/0.7907/0.7012）——"全部叶子均值无梯度"是稀疏监督评估假象
- **正确打分指标 = 目标词叶子激活**（词→叶子映射），评估脚本 slu_sit_eval_target_leaf_v1.py、完整打分脚本 slu_sit_score_collection_v1.py
- 真实坐姿样本：pos 完整打分 22.3→27.1（用户实测 0 分样本 4.9→15.3，3 倍）；neg ~0 分无误判；⚠️ 花样本下降（41.4→21.5）

### 待办（报告 §7）
1. 真实坐姿 pos 样本扩充（当前仅 9）——待主管安排采集
2. 可选 S1 调权重训（--sit-s1-weight）
3. onnx 导出 tree_model_v6.4.onnx 全链路回归
4. 坐姿增强审核网页已提交用户人工确认（数据增强人工复核 A/B/C/D）

### 审核网页
- 数据增强人工复核（A/B/C/D 四类）：http://127.0.0.1:8151/index.html（8150 旧端口可能带缓存）
- 服务脚本：scripts/http_serve_no_cache.py（no-cache + 多线程）；生成脚本 scripts/slu_data_aug_review_page_v6.py
- 硬更新规范：开新端口绕浏览器缓存（公共约束 §10）

### 工具环境
- python：/home/wuyangcheng/myenv/bin/python3.10（numpy/matplotlib/torch）
- GPU 训练：zhuhai（ssh，172.28.17.71:7712，gen env python；**GPU0/1 均被外人占用一律禁用，用 GPU2-9 弹性池 g29/g34/g56/g78**，训练前先 nvidia-smi 确认目标卡空闲，换卡先报主管）
- 训练日志即时输出：v4 脚本已加 print flush + TensorBoard

## 其他
- 公共约束/组织架构：/data/WYC/signLanguage/.team/team_constraints.md（§8 架构、§9 dashboard、§10 开新端口、§4 记忆互通）
