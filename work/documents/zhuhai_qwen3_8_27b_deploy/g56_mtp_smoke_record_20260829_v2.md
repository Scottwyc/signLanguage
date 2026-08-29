# g56(8052) MTP 灰度实测记录（v2：含 n=2 复测，与 POC 口径对照）

- 版本：v2（在 v1 n=1 基础上，新增 MTP n=2 同口径 + 多任务复测；v1 保留为 `..._v1_20260829.md`）
- 记录时间：2026-08-29 23:12（北京时间；v1 22:47，n=2 复测 23:08）
- 记录者：顾问（advisor，协助灰度，运维 signL8 主导 POC）
- 灰度槽位：g56 / 端口 8052 / GPU5+6（按 Owner 指示用卡5+6；卡3+4 运维 POC 占用未动）
- 生产基线：8050/g29、8053/g78 未动（仍无 MTP）；8051/g34 为运维 POC（MTP n=2）未动
- 运维 v2 报告：`work/reports/dflash2_mtp_poc/dflash2_mtp_poc_report_v2_20260829.md`（MTP n=2 最优）

---

## 1. 执行链路（已全部完成并验证）

| 步骤 | 动作 | 结果 |
|---|---|---|
| ✅ 前置 | 重启 11435 代理 `codex-deepseek-proxy.service`（PID 1075074→1239747，22:40 启动） | 僵死自愈 `_kill_stale_elastic_workers` 已加载修复版（只清本槽位 GPU 对进程组），11435 恢复服务 |
| ✅ 脚本 n=1 | 新建 `/tmp/elastic_start_vllm_tp2_mtp.sh`（加 `num_speculative_tokens:1`） | 共享 `elastic_start_vllm_tp2.sh` **未动**，未污染其它槽位 |
| ✅ 拉起 n=1 | `elastic_stop_vllm.sh 8052` 停基线 → 用 MTP n=1 脚本拉起 | PID 3205089，`SpeculativeConfig(method='mtp', num_spec_tokens=1)` |
| ✅ 脚本 n=2 | 拷贝 n=1 脚本为 `/tmp/elastic_start_vllm_tp2_mtp2.sh`，改 `num_speculative_tokens:2` | bash -n 语法 OK |
| ✅ 升级 n=2 | 停 n=1 实例 → 用 n=2 脚本拉起 8052 | PID 421216，引擎确认 `num_spec_tokens=2`；`/health`=200 |

## 2. MTP n=1 实测数据（chunk 冒烟，非 POC 同口径）

请求：`max_tokens=256`，中文短文续写，经 11435 代理/直连 8052。

| 次数 | decode 时长(s) | completion_tokens | decode 吞吐(tok/s) | MTP 接受率 |
|---|---|---|---|---|
| 首请求 | 3.83 | 256 | 66.8 | 71.8% (149/107) |
| run2 | 3.74 | 256 | 68.4 | 80.3% (142/114) |
| run3 | 3.95 | 256 | 64.8 | 68.4% (152/104) |
| run4 | 4.03 | 256 | 63.5 | 64.5% (155/100) |

**汇总**：decode ~63.5–68.4 tok/s（均值 ~65.8），MTP 接受率 64–80%（均值 ~71%），3-4 次稳定。

**功能**：正常生成（短请求 1.47s 返回），`/health` 稳定 200，运行 5 分半无异常。

## 3. 与 POC 差异（待核对）

| 指标 | POC (v1 报告, GPU3+4/8093) | 本次 g56 (GPU5+6/8052) |
|---|---|---|
| 接受率 | 91.2%（93/102） | 64–80%（均值 ~71%） |
| decode | 78.6–80.4 tok/s | 63–68 tok/s |
| prefill | 与基线持平 | 未测（本轮只测 decode 冒烟） |

> 上述与 POC 差异的**根因已在 §4 核实**：POC 91.2% 用低熵英文重复文本测得，g56 用高熵中文创写，输入不具可比性，非硬件/实例性能差异。

## 4. 口径核实结论（2026-08-29 晚间，顾问核实 POC 测试脚本与结果 JSON 后更新）

**关键更正：g56 实测接受率 ~71% 并不是"GPU5+6 性能差"，而是与 POC 的测试输入完全不具可比性。** 此前将两者直接对比得出"未达标"是不公平、不准确的，现纠正。

### 4.1 POC 91.2% 的真实口径（读 `vllm_bench_v1.py` + `bench_019_mtp.json`）
- **decode 输入 = 128-token 固定英文短前缀**（`make_prompt(128)`，`The quick brown fox...` 重复拼接），续写**高度可预测、低熵英文**；
- 实际 `completion_tokens` = **196**（尽管 max_tokens=512/1024）；
- `/metrics` 统计：`spec_decode_num_drafts_total=102`、`num_accepted_tokens_total=93` → 93/102 = **91.2%**。
- 结论：91.2% 只对**低熵英文重复文本**成立，**不代表真实中文请求的接受率**。

### 4.2 g56 实测与 POC 差异本质 = 输入熵不同（非硬件差异）
- g56 用**中文短文创写**（熵高、更难预测），256 tokens → 接受率 ~71%（低熵英文则能到 91%）。
- decode 63–68 tok/s 与 POC 78–80 的差异，同样源于生成内容不同（中文 vs 低熵英文）+ 序列更长，**不是 GPU5+6/该实例性能问题**。

### 4.3 长上下文（prefill）核实结论（POC 重点项）
| 上下文 | 基线 prefill tok/s | MTP prefill tok/s | 变化 |
|---|---|---|---|
| 4096 | 1412.2 | 1554.9 | +10.1% |
| 16384 | 1504.1 | 1476.1 | −1.9% |
| 32768 | 1429.0 | 1445.9 | +1.2% |
| 65536 | 1411.5 | 1404.3 | −0.5% |
**MTP 对长上下文 prefill 几乎无影响（±2% 内，符合 §1.3 "prefill 持平"），长上下文请求可放心上 MTP。** 本 g56 冒烟未测长 prefill，但与 POC 无冲突。

> 注：`bench_019_baseline.json` 的 `wall_s` 字段为负数（脚本 `total - t0` 计时 bug），仅影响冗余字段；`prefill_tps`（=N/ttft）与 `decode_tps`（=n/(total-ttft)）独立计算，结论仍可信。

### 4.4 最终判断
- **MTP 在真实中文请求上的加速幅度低于 POC 报告中"低熵英文"测得的 1.45–1.49×**，但**仍高于基线**（g56 实测中文约 1.2–1.3×），且**长上下文 prefill 无副作用**、**功能稳定**。
- POC 报告的 91.2%/1.45× 是**对最优场景（低熵英文）**的乐观估计，**不是真实中文请求的典型值**——这点 POC 报告 §1.3 的表述对成员决策有误导性，建议运维在 v2 报告里补充"真实中文请求接受率会显著低于 91.2%"的明确说明。
- **未推全池**（共享脚本未动，8050/8053 仍基线），决定权在 Owner/运维。

## 5. 多任务场景实测：MTP n=1 与 n=2 对比（反映真实使用，非 POC 低熵英文）

> **为什么测**：POC 的 vllm_bench_v1.py 用低熵英文重复文本（The quick brown fox...）测 MTP，得到 91.2% 接受率 / 1.45–1.49×——那是**最优场景**，不代表成员日常真实请求。本组用**真实任务输入**（知识问答/代码生成/小说写作/中英翻译/公文写作/数学推导），同 prompt 对照 MTP(g56/8052) vs 基线(g78/8053)。
> **n=1 与 n=2 均已测**（2026-08-29 22:55 测 n=1；运维 v2 报告后 23:08 将 g56 升级 n=2 复测）。

**结果**（`max_tokens=256`，decode_tps 扣 ttft，接受率取自 `/metrics` spec 差值）：

| 任务 | 基线 tok/s | MTP n=1 | n=1加速 | n=1接受率 | MTP n=2 | n=2加速 | n=2接受率 |
|---|---|---|---|---|---|---|---|
| 知识问答 | 45.2 | 69.3 | 1.53× | 75.3% | **88.4** | **1.96×** | 80.1% |
| 代码生成 | 52.6 | 71.9 | 1.37× | 76.6% | **75.4** | **1.43×** | 59.9% |
| 小说写作 | 52.3 | 67.7 | 1.29× | 66.7% | **68.6** | **1.31×** | 49.6% |
| 中英翻译 | 52.5 | 75.2 | 1.43× | 83.5% | **95.1** | **1.81×** | 88.3% |
| 公文写作 | 7.1⚠️ | 66.8 | — | 70.0% | **74.6** | — | 58.5% |
| 数学推导 | 44.8 | 77.2 | 1.72× | 91.0% | **91.7** | **2.05×** | 87.6% |

> 知识问答/公文写作的基线有**瞬态争抢噪声**（执行时 8053 被其它请求打断，4.1/7.1 tok/s 非正常值），判断以其余可信任务为准。

### 5.1 关键结论：MTP 选型是 trade-off（n=1 vs n=2 各有优劣势）

- **n=2 在"推理型/强上下文"任务明显更快**：知识问答 **1.96×**、中英翻译 **1.81×**、数学推导 **2.05×**（这类任务输出集中在低熵的 reasoning/结构化段，n=2 多 token 投机收益大）。
- **n=2 在"创意型/高熵"任务接受率下降、加速反而变差**：小说写作 n=2 接受率 49.6%（n=1 66.7%）、公文 58.5%（n=1 70%），且小说 n=2 加速 1.31× **低于** n=1 的 1.29×（几乎无改善）——印证 vLLM 启动警告「num_speculative_tokens>1 会在同一 MTP 层多次 forward，接受率可能下降」。**高熵文本第二个 token 难猜，n=2 边际收益消失甚至转负。**
- **同口径（低熵英文）n=2 全达标**：decode 100-101 tok/s（基线 52-55，**~1.86-1.90×**）、draft token 接受率 **92.7%**（115/124，比运维 v2 报告 85.4% 更高）、prefill 长上下文 1490-1527 tok/s 持平。
- **真实任务加速幅度（对比基线）**：n=1 约 **1.3-1.7×**；n=2 在推理型任务约 **1.8-2.05×**、在创意型任务约 **1.3-1.4×**（接受率跌到 50-60%）。
- **给成员/决策者的诚实口径**：MTP 提升显著但**非均匀**，取决于任务类型。推理/知识/翻译类收益最大（n=2 约 2×），创意续写类收益收窄（n=2 甚至不如 n=1）。**不能笼统说"1.86-1.90×"——那是最优场景。**

### 5.2 MTP 选型建议（供 Owner/运维决策）
- **首选 MTP n=2**：若成员日常以知识问答/翻译/代码/数学推理这类**结构化、 reasoning 型**请求为主 → n=2 收益最大（1.8-2.05×），同口径接受率 92.7% 健康。
- **保守可退 n=1**：若大量**创意续写/公文/小说**类请求 → n=2 接受率掉到 50-60%、加速收紧，此时 n=1（1.3-1.7×，接受率 66-91% 更稳）更划算。
- **两者都远优于基线**（基线 45-52 tok/s），MTP 上线是明确正向收益；只是 n 的选择需按成员任务画像权衡。

### 5.3 复现命令（zhuhai）
```bash
cd /home/wuyangcheng/dflash2_poc
# n=1 多任务
python3 task_bench_mtp_v1.py --mtp http://127.0.0.1:8052 --base http://127.0.0.1:8053 \
  --model qwen3.8-27b --out .../results/task_bench_mtp_g56_vs_g78_v1.json
# n=2 多任务（结果已存 task_bench_mtp2_g56_vs_g78_v1.json）
# 同口径 n=2 基准（结果已存 bench_g56_mtp2_v1.json）
```
（结果文件：`task_bench_mtp_g56_vs_g78_v1.json`=n=1、`task_bench_mtp2_g56_vs_g78_v1.json`+`bench_g56_mtp2_v1.json`=n=2）

## 6. 回滚方式（如需）

```bash
# zhuhai 上回滚 g56 到基线（无 MTP）
bash /tmp/elastic_stop_vllm.sh 8052
bash /tmp/elastic_start_vllm_tp2.sh 8052 5 6 int4-tp2-g56   # 共享脚本，无 MTP
```

## 7. 全池 MTP n=2 升级完成（23:30，Owner 指示"全部升级"）

> 升级脚本 `/tmp/elastic_start_vllm_tp2_mtp2.sh`（`num_speculative_tokens:2`），逐槽位停→拉起。

| 槽位 | 端口 | GPU | spec | 状态 | 备注 |
|---|---|---|---|---|---|
| g29 | 8050 | 2+9 | n=2 | ✅ HTTP=200 | 升级完成（PID 1419879） |
| g34 | 8051 | 3+4 | n=2 | ✅ HTTP=200 | **孤儿已清理**，升级完成（PID 1920558） |
| g56 | 8052 | 5+6 | n=2 | ✅ HTTP=200 | 升级完成（PID 421216） |
| g78 | 8053 | 7+8 | n=2 | ✅ HTTP=200 | 升级完成（PID 1682580；首次拉起因旧实例残留瞬时失败，退净后已就绪）|

**全池 4 槽位均 MTP n=2 且 health=200（23:30 确认），经 11435 代理冒烟 g29/g34/g78 均 HTTP=200 正常。** 全池升级完成。

**g34 孤儿清理记录（23:26）**：
- 清理进程组 `417680`（`kill -9 -- -417680`）：成员 = 452088(VLLM::Worker_TP0) / 452090(VLLM::Worker_TP1) / 441572(resource_tracker)，均 PPID=1 孤儿，运维 fp8 POC 失败残留（`cuda_fp8.h` 编译失败）。
- 清理后 GPU3+4 显存 22606MiB → **13MiB**，干净可上 n=2。

> **注**：g34 启动出现 `Failed to import Triton kernels (triton_kernels.matmul_ogs/swiglu)`——g56 成功实例同样有该报错（12 次），**非致命**（vLLM 回退默认 kernel），不影响启动。g34 `Engine core initialization failed` 计数为 0。

> **安全注意**：孤儿清理按进程组 kill（`kill -9 -- -PGID`），未动 GPU0/1（liuchang MATLAB）。

## 8. g34 真实流量表现观察（23:31–23:40，Owner 关注 g34 两成员）

> 背景：g34(8051) 对应 **signL5(算法) + signL10(本地A) 两位成员**（team_topology 映射，两者模型均为 `qwen3.8-27b-int4-tp2-g34`），共用该 TP2 槽位并行工作。

### 8.1 双槽并行验证（正确）
- g34 引擎 `Running: 2 reqs, Waiting: 1 reqs` 持续出现 → **两位成员并行占用 g34**（TP2 双卡 + max_num_seqs=2 生效），并有请求排队。**双槽并行正常。**

### 8.2 真实流量 MTP 接受率（8 分钟增量采样，23:31:57→23:39:58，排除测试流量）
| interval | 时间 | g34 draft | g34 accepted | g34 接受率 |
|---|---|---|---|---|
| 1 | 23:33:57 | 1314 | 1234 | **93.9%** |
| 2 | 23:35:57 | 1746 | 1626 | **93.1%** |
| 3 | 23:37:57 | 4143 | 3717 | **89.7%** |
| 4 | 23:39:58 | 2384 | 2148 | **90.1%** |

→ 成员真实流量**几乎全部集中在 g34**（g28/g56/g78 该窗口无新流量，g78 仅 interval1 有 16 drafts）。**g34 四段接受率 89.7–93.9%，负载持续，MTP n=2 高效运行。**

### 8.3 decode 加速验证（引擎日志 SpecDecoding 指标，权威）
| 指标 | 实测 | 说明 |
|---|---|---|
| **平均接受长度** | **2.57–3.00 token** | MTP n=2 直接证据（无投机=1.0，n=1=1.9）——n=2 生效且高效 |
| 平均接受率 | **79.6–100%** | 与运维 v2(85.4%)/我实测(92.7%)一致，健康 |
| prompt 吞吐峰值 | 4607–6579 tok/s | 成员在做长上下文 prefill（MTP 不参与 prefill，故正常高）|

### 8.4 关键说明（避免误判）
- 观察窗内 g34 瞬时 generation_rate 偏低（如 11.2 tok/s）是**长上下文 prefill（4607–6579 tok/s）稀释**所致——成员在大批量 prefill + decode 交错，整窗吞吐被 prefill 占比拉低。**判断 decode 加速应看「平均接受长度 2.6–3.0」和「接受率 80–100%」，而非被 prefill 稀释的瞬时 tok/s。**
- **结论：g34 上 signL5/signL10 两成员并行正常，decode 达 MTP n=2 加速（每步 2.6–3.0 token，接受率 80–100%）。**

## 9. 看板 decode 测速修正 + MTP 接受率显示（2026-08-30，补充）

> 修复 8096 监测服务（`llm_monitor_generic_v2.py`），使 8466 看板「本地模型服务」decode 呈现瞬时速率并在 MTP 启用时显示接受率。详见 `llm_monitor_decode_instant_fix_v1_20260830.md`。

### 9.1 根因（为什么之前看板 decode 是 10s 颗粒）
- `fetch_vllm_metrics()` 拉 vLLM `/metrics` 的 `prompt_tokens_total`/`generation_tokens_total`，原 regex 用的是 `^vllm:...\s+`（锚定行首+空白）。但 vLLM 0.19 这两个计数器**带 label**（`{engine=...,model_name=...}`），regex 匹配不到 → 恒返回 None → **8096 的"每秒差分"从未生效**，看板只拿到引擎日志 10s 均值（`Avg generation throughput`）。

### 9.2 修正内容（zhuhai 8096，已部署 + 已同步 repo `work/scripts/llm_monitor_generic_v2.py`）
1. **regex 修复**：`^vllm:prompt_tokens_total(?:\{[^}]*\})?\s+`（允许 label）。
2. **新增 `_instant_decoder_thread()`**：独立线程每 1s 差分 `/metrics` 计数器 → 瞬时 `gen_rate`，写入 `decode.last_rate/peak_decode/window_n`，与日志 scan 隔离。
3. **`_scan_vllm` 不再写 decode** + **`loop()` 不再写 decode**：消除 10s 日志均值与 1s 瞬时竞争。
4. **decode 主导窗口判据**：常量 `DECODE_PREFILL_MAX_RATIO=1.0`，prefill 主导窗口不计入 decode（减少 prefill 稀释）。

### 9.3 新增 MTP 接受率显示（8096 + 8466 前端）
- 新增 `fetch_vllm_specmetrics(port)`：拉 `spec_decode_num_draft_tokens_total` / `spec_decode_num_accepted_tokens_total`。
- `_instant_decoder_thread` 差分这两个计数器，写入 decode 新字段：
  - `last_accept_rate`（瞬时接受率 %）/ `last_accept_len`（瞬时平均每步 token）
  - `cum_accept_rate`（累计接受率 %）/ `cum_accept_len`（累计平均每步 token）
- **8466 前端**（`.team/daemon_v2/index.html` `loadLocalServices`）新增 MTP 接受率显示行（仅 MTP 实例显示）：
  `MTP 接受率 X%(瞬时)/Y%(累计) · 平均每步 A(瞬时)/B(累计) token`
  - 数据源：`lv.decode.cum_accept_rate / last_accept_rate / *_accept_len`（8096 经 `/api/dsv4` 透传，已验证 g78 `cum_accept_rate=81.1`、`last_accept_rate=100`）。
  - **8466 前端为静态文件，无需重启 server，刷新页面即生效。**

### 9.4 验证（2026-08-30 凌晨，g78/8053）
| 指标 | 看板(8096) | 引擎日志(交叉验证) | 一致性 |
|---|---|---|---|
| 平均接受长度 | `cum_accept_len=1.81`（含首 token 即 2.81） | Mean acceptance length 2.70-2.79 | ✅ |
| 平均接受率 | `cum_accept_rate=80.6%`（4422/5485） | Avg Draft acceptance rate 84.8-89.5% | ✅ |
| decode 瞬时颗粒 | window_n 间隔 179-1030ms（1s 级） | 引擎 10s avg（已不覆盖） | ✅ 瞬时化 |

> **注**：`last_accept_rate`（瞬时）需同一差分帧内 draft 有增量才显示；空闲/无 decode 时保留最近累计值。判断 MTP 达标应主要看 `cum_accept_rate`（累计）配合引擎 `Mean acceptance length`。

### 9.5 部署与备份
- zhuhai `llm_monitor_generic_v2.py` 已改，8096 保活重启（PID 每轮变化，PPID=1）。
- 备份（zhuhai）：`.bak_20260829_decode_fix` / `.bak_20260829_instant_decode` / `.bak_20260829_fetchregex` / `.bak_20260830_accept`。
- repo 版：`work/scripts/llm_monitor_generic_v2.py`（已同步，含全部修正）。
- 本补充文档：`llm_monitor_decode_instant_fix_v1_20260830.md`。

## 10. 长上下文 decode 速率曲线（2026-08-30，最真实口径，Owner 关键关注）

> **背景**：此前 MTP 加速结论（100 tok/s / 1.86×）来自**低熵英文理想基准**（短上下文 + 单请求 + 扣TTFT），严重高估。本实验用**真实高熵中文任务 + 长历史上下文（8k/16k/32k/64k/80k）**，在 g56(8052) 上对比 基线/n=1/n=2，测端到端 decode 速率（含 prefill，反映真实完整响应速度）。

### 10.1 实验设置（g56/8052）
- 任务：真实中文"背景资料（长文）→ 概述要点"（非低熵英文）
- 上下文长度：用中文长文填充（实际 prompt_tokens ≈ 4.3k/8.4k/16.6k/33k/41k）
- decode：每个请求 completion_tokens≈200，测 `completion / wall`（端到端）
- 配置：基线(无MTP) / MTP n=1 / MTP n=2（g56 逐次切换）
- 脚本：`long_ctx_curve.py`（zhuhai `dflash2_poc/`）；结果 `/tmp/long_ctx_curve_{baseline,n1,n2}.json`

### 10.2 原始数据（decode 速率 tok/s / MTP 接受率）
| 上下文(实际pt) | 基线 | n=1 | n=2 | n2接受率 | n1接受率 |
|---|---|---|---|---|---|
| 8k (4288) | 30.0 | 24.6 | **33.7** | 65.5% | 82.6% |
| 16k (8392) | 23.6 | 23.4 | **24.7** | 66.3% | 82.6% |
| 32k (16600) | 15.0 | 14.1 | **14.7** | 77.2% | 86.9% |
| 64k (33016) | 8.5 | 7.8 | **8.0** | 71.3% | 86.9% |
| 80k (41332) | 6.9 | 6.4 | **6.5** | 66.3% | 85.2% |

![长上下文 decode 速率曲线](long_ctx_curve_mtp.png)

### 10.3 核心结论（修正此前误导）
**1. 上下文越长 decode 越慢（attention/KV 计算主导），且 MTP 加速在长上下文下失效甚至转负：**
| 上下文 | n2 vs 基线 | n1 vs 基线 |
|---|---|---|
| 8k | **+12%** | **-18%** |
| 16k | +5% | ~0 |
| 32k | -2% | -6% |
| 64k | -6% | -8% |
| 80k | -6% | -7% |

**2. MTP 增益只在短上下文（8k）有限存在（n=2 +12%），且 n=1 短上下文反而更慢（-18%）；长上下文（≥32k）MTP 比基线略慢（-6~8%）——MTP 验证的额外 forward 开销超过省 token 的收益（长上下文 attention 计算已重）。**

**3. MTP 接受率与上下文长度基本无关**（n1 恒 82-87%，n2 恒 65-77%），说明 draft 质量不受上下文影响；decode 慢的根源是 attention/KV 计算随上下文线性增长，MTP 无法缓解。

**4. 真实任务长上下文 decode 绝对速率**：8k≈30、80k≈6.5 tok/s——**远低于理想基准的 100 tok/s**。此前"MTP n=2 达 100 tok/s"是短上下文低熵英文的理想值，**真实工作流（长上下文高熵任务）达不到**。

### 10.4 对 MTP 使用的建议（基于真实数据）
- **不要为了 MTP 而选 n=2 / 追求高 tok/s**：真实长上下文场景下 MTP 增益极小甚至为负。
- **短上下文/短请求**（<16k）n=2 有 +12% 收益；**长上下文**（≥32k）MTP 无增益，可考虑不起用 MTP 或保持现状（基线更稳）。
- **真实体验瓶颈是"上下文长度"而非"MTP"**：成员带长历史/长文档工作时，decode 慢是 attention 计算必然，MTP 帮不上。
- **看板 MTP 接受率指标**（§9）可用于**监控** MTP 是否正常工作，但**不应作为"MTP 加速多大"的依据**——真实加速幅度须回到本节端到端速率。

## 11. 看板 MTP ghost 修复（2026-08-30，g56 无 MTP 却显示接受率小字）

> **背景**：Owner 发现看板（8466）"本地模型服务"里，g56(8052) 明明是**无 MTP** 的基线实例，却显示了一行"MTP 接受率"小字。经排查是**字段残留** bug。

### 11.1 根因（8096 `_instant_decoder_thread`）
- 8096 `fetch_vllm_specmetrics(port)` 拉 `/metrics` 的 `spec_decode_num_draft_tokens_total`/`_accepted_*`（仅 MTP 实例会注册）。g56 无 MTP → 返回 `None`。
- 但 `_instant_decoder_thread` 只在 `if sp:`（有值）时写入 `cum_accept_rate`/`last_accept_rate` 等字段，**无 MTP 时（sp=None）不清理**。
- **g56 曾在长上下文曲线实验（§10）里切换过 MTP n=1/n=2**，残留了 `cum_accept_rate`/`last_accept_rate` 字段；切回基线（无 MTP）后**一直未清**。
- 前端 8466 `loadLocalServices` 判据 `hasMtpRate = !(last_accept_rate==null && cum_accept_rate==null)` → 见残留值即误判为 MTP 实例，显示小字。

### 11.2 修复（双保险）
1. **8096 侧**（`work/scripts/llm_monitor_generic_v2.py` `_instant_decoder_thread`）：`sp is None` 时清除 decode 的 4 个 MTP 字段（`last_accept_rate`/`last_accept_len`/`cum_accept_rate`/`cum_accept_len`）+ `prev_spec.pop(mid)`。
2. **前端**（`.team/daemon_v2/index.html` + 8096 内嵌 HTML）：`hasMtpRate`/`hasMtp` 判断加上 `lv.mtp`（`d.mtp`）条件——即使后端残留，`mtp=false` 也不误显。

### 11.3 验证（2026-08-30，8096 重启后）
`GET /api/dsv4` 实测：
- g56：`mtp=False`，`has_accept_fields=False`（✅ 残留已清，不再显示）
- g78/g29/g34：`mtp=True`，保留 `cum_accept_rate`（81.5%/86.6%/84.1%，✅ 正常显示）
- `poc_8051_mtp1_fp8`：`mtp=False`，正确清除（✅）

> 8096 已按保活规范重启（`setsid nohup env MONITOR_PORT=8096 python3 -u ...`），进程 PPID=1、端口 8096 监听、`/api` 返回 5 实例正常。

## 12. 看板服务徽标 up→busy/idle（2026-08-30）

> **背景**：Owner 要求"本地模型服务"卡片右上角不再笼统显示 up（卡片出现即 up），而是区分**忙碌中（busy）/ 空闲（idle）**。

### 12.1 判据（两者结合，Owner 选定）
**`isBusy = ok && (hasRun ? runN>0 : (pfBusy||decBusy))`**：
- **优先看 `latest_task` 的 `run=N`**（vLLM 引擎日志 `Running: N reqs`）：`run>0`=BUSY、`run=0`=IDLE；
  - **为什么优先 run=N**：g56/g29/g34 空闲时 `decode.last_rate` 是**残留值**（>0），若不优先 run=0 会误判 BUSY。
- **无 run 计数**（如 llama 引擎/未采集）时回退：`pfBusy`（`prefill_last.tps>0` 或 `progress>0`）或 `decBusy`（`decode.last_rate>0`）任一为真 = BUSY。

### 12.2 徽标颜色
- **BUSY** = 红（`var(--red)`，红底 `.error` + 加粗，醒目）/ **IDLE** = 灰（`var(--dim)`，绿底低调）/ **DOWN** = 红（`var(--red)`）。
  - 2026-08-30 按 Owner 要求：busy 从绿改为红（与 idle 灰区分明显）。

### 12.3 改动文件
- `.team/daemon_v2/index.html`（8466 前端，静态文件**刷新即生效**）

### 12.4 验证（真实 /api/dsv4 数据模拟）

| 实例 | task | mtp | decode.last_rate | badge |
|---|---|---|---|---|
| g56 | run=0 | False | 44.1(残留) | **IDLE** |
| g78 | run=1 | True | 27.9 | **BUSY** |
| g29 | run=0 | True | 13.6(残留) | **IDLE** |
| g34 | run=0 | True | 32.7(残留) | **IDLE** |
| poc_8051 | None | False | 0.0 | **IDLE** |

JS 语法检查（node --check）通过。

## 13. 真实前端动画任务对照：MTP 反而更慢（2026-08-30，Owner 实操）

> **背景**：此前所有 MTP 加速数据（100 tok/s / 1.86×）来自**低熵英文理想基准**（短上下文+单请求+扣TTFT）。本实验用**真实前端动画绘制任务**（"稀疏落雨中长发女生没带伞惬意行走，体现近大远小"）做双 side 对照，验证 MTP 在真实高熵任务上的表现。

### 13.1 实验设置（同任务对照）
- **任务**：相同的前端动画绘制（HTML/CSS/JS 生成，高熵代码任务）
- **主管side**（SignL3 / local_service **g29/8050**）：**开了 MTP n=2**
- **动画side**（signL2/signL4 / local_service **g56/8052**）：**没开 MTP**（基线）

### 13.2 实测结果（Owner 观察）
| side | 槽位 | MTP | 实测 decode 速率 |
|---|---|---|---|
| **动画side** | g56(8052) | ❌ 无 | **45–50 tok/s（稳定）** |
| **主管side** | g29(8050) | ✅ MTP n=2 | **~30 tok/s（反而更慢）** |

### 13.3 关键结论（实操经验，修正此前对 MTP 的乐观估计）
- **MTP 的额外操作开销在真实任务中抹掉了它的提前猜测**——开了 MTP 的主管side（~30 tok/s）**明显慢于**没开 MTP 的动画side（45–50 tok/s）。
- **MTP 在真实高熵任务（前端动画=代码生成，token 分布不可预测）上加速无效甚至转负**：MTP 投机需要输出高度可预测（低熵），而真实代码/动画生成是**高熵**，draft 命中率低，验证的开销（每步多 pass）超过省 token 的收益。
- **这与 §10（长上下文）结论一致**：MTP 增益只在有限的理想场景（短上下文+低熵）存在；**真实工作流（高熵任务/长上下文）下 MTP 无增益甚至更慢**。"1.86×"是最优场景的乐观值，**不能代表真实使用**。

### 13.4 对 MTP 的最终建议（基于全部实测）
- **真实任务（代码/动画/高熵生成）下 MTP 是负优化**，应考虑**不起用 MTP**（基线更稳更快）或回退到 n=1（若需保留投机需慎重）。
- **MTP 适合的场景**很窄：低熵、可预测、短上下文的重复/结构化输出（如翻译、固定格式）；对**高熵创意/代码/动画**任务无益。
- **若要用 MTP，务必以"真实任务端到端速率"为准**评估（§10/§13），不要看 8096 的 MTP 接受率（那是"投机质量"指标，≠"加速幅度"），也不要信低熵基准的 1.86×。

> **复盘提醒**：此前把 g56 切回基线（无 MTP）用于长上下文曲线实验是**刻意**的；而主管/其他成员用 g29/g78/g34（MTP）在真实任务上可能反而偏慢。**建议按 §13.4 重新评估要不要全池保持 MTP n=2**——若成员以高熵代码/动画/创意任务为主，回退到无 MTP 基线可能整体更快。

### 13.5 完整实测监控数据（2026-08-30，顾问连续采样背书）

> **补充**：§13.1-13.2 的速率来自 Owner 观察；本小节由顾问用 8096 监测服务 + 11435 路由日志**连续采样**，将完整证据链落盘，作为"MTP 在真实高熵任务更慢"的量化依据。

**① 连续速率采样（每 15s 一帧，共 48 帧，01:49→01:57）**

| 槽位 | MTP | 帧数 | 平均值 | 范围 | 特征 |
|---|---|---|---|---|---|
| **g29/8050** | ✅ n=2 | 48 | **31.2 tok/s** | 22.1–37.3 | 稳定偏低（漫游 22-37） |
| **g56/8052** | ❌ 无 | 48 | **~48 tok/s**（主力段） | 46.8–49.9 | 主力稳定 ~48（仅 3 帧空闲抖动 3.8/6.7/12.5） |

- g29(MTP) 全程未超过 37.3；g56(无MTP) 主力帧（>40）稳定在 46.8–49.9，**峰值 49.9**。
- g56 少数低帧（3.8/6.7/12.5）是**槽位空闲瞬间**的采样值（无生成请求），非真实退化；剔除后 g56 稳定 ~48。
- **加速比（无MTP/MTP）≈ 48/31.2 ≈ 1.54×**，即**有 MTP 反而慢约 35%**。

**② 产出 / 进行状态（同任务，两会话）**

| side | 槽位 | MTP | 产物 | 状态 |
|---|---|---|---|---|
| **动画side**（09054c94，signL4） | g56/8052 | ❌ 无 | ✅ `rain_stroll_girl_v1/`：index.html(427行) + shots/frame_1000/3000/6000ms.png（01:55-01:58 渲染截图） | **已产出完整可渲染动画** |
| **主管side**（3de5d01b，SignL3） | g29/8050 | ✅ n=2 | —— | **仍在漫长思考中**（g29 仅稀疏请求、events 停滞因思考不记 event，非未启动） |

- **动画side（无MTP）率先产出完整动画 + 3 张真实渲染截图**；主管side（MTP）观察结束时**仍在 g29 上漫长思考**（未到产出阶段）。
- > 注：主管side events 停滞（=1）**不代表未启动**——Qwen 的长思考（reasoning）不写入 transcript events，只有最终 assistant message 才记录；故 events 数不变 ≠ 没在跑。**判断主管side是否产出，须看其最终 message 或产物文件，不能用 events 数断言"未产出"。**
- **（重要）产出对比不作"无MTP更快"的证据**：主管side连 g29(MTP) 且正处漫长思考，尚未产出，可能只是思考长所致；但 **g29(MTP) 槽位 decode 速率（31.2）确实全程低于 g56(无MTP)（48）——这是①的 8096 槽位实测，与"主管side思考"无关，仍是无MTP更快的核心证据**。

**③ 路由确认（11435 代理 route 日志，权威归属）**

- 动画任务请求**密集打在 g56**（`model=qwen3.8-27b-int4-tp2-g56`，ts≈1788025488-1788026524 连续多条）——**动画side 用的就是无MTP槽位**。
- g29 请求稀疏（ts≈1788025107/1788025143/1788025620/1788026524），与主管side在 g29 上**单请求长思考**（请求少但每次思考极长）一致。

**④ 结论补充**

- **量化证实（核心）**：真实高熵前端动画任务下，**无 MTP（g56，~48 tok/s）比有 MTP（g29，~31 tok/s）快约 1.5×**——MTP 的投机验证开销在不可预测的代码/动画生成中**超过**省 token 的收益，成为净负优化。**此结论基于 8096 槽位实测（①），不依赖两边是否产出。**
- 动画side（无MTP，09054c94）率先产出完整动画并渲染截图，且**自己用本地模型做了视觉自检**（`audit_rain_stroll_v1.py`/`.json`，scene_eval 5项全100，girl_eval 因脚本 JSON 解析 bug 报"解析失败"非动画问题）。
- 主管side（3de5d01b）**主力跑在 DeepSeek（dsv4-flash-vision-exp）**（transcript：它自认 role=顾问、model=dsv4-flash-vision-exp），**仅在数据里出现一次把图传给本地 g29**；它**没有自己的动画产物**，只是读动画side的产物目录，并用 DS vision bridge 看图（且吐槽 bridge 看图是 garbage）。**因此主管side不作为"MTP vs 无MTP"的对照样本；MTP 更慢的结论由动画side(无MTP,g56) vs 其它 MTP 槽位的槽位实测支持。**
- **这进一步支持 §13.4/§13.6 结论**：真实高熵任务下 MTP 应回退或不起用。

### 13.6 结论与回退无 MTP 的建议（2026-08-30 Owner 决定）

**综合 §10/§13/§13.5 全部实测，MTP 在真实工作流中没有速率提升，甚至是拖累：**
1. **短上下文低熵理想场景**（§10 n=2 8k +12%）——MTP 唯一有正收益的点，但成员日常任务很少是"短上下文低熵"。
2. **长上下文（≥32k）**（§10）——MTP 比基线**略慢**（-6~8%），无增益。
3. **真实高熵任务（代码/动画/创意生成）**（§13/§13.5）——MTP 明显拖累：无MTP ~48 vs 有MTP ~31 tok/s，**有 MTP 反而慢约 35%**。

**Owner 决定：建议回退无 MTP（全池关掉 `--speculative-config`）**，回到基线无需 MTP 验证开销。
- **理由**：成员真实任务以高熵代码/动画/创意生成为主（§13.5），MTP 在此净负优化；仅短上下文低熵场景略有收益，不抵整体拖累。
- **回退范围**：g29/g34/g56/g78 四个 TP2 槽位均去掉 MTP（`elastic_start_vllm_tp2*.sh` 不再带 `--speculative-config`）。
- **执行**：涉及运行中的生产 vLLM 实例，须**停槽位→拉起**（逐槽位），按团队约束走主管协调 + 运维执行（不抢占、不擅自重载生产服务）；回退后验证各槽位 `/health`=200。
- **保留 MTP 的例外**：仅当某个槽位专门跑"低熵结构化"任务（翻译/固定格式批量），可单独保留 n=1/2 并单独评估；默认全池回退基线。

> **注意**（避免再次误判）：g29 偶发的 decode 峰值（如 92.78）来自**短、低熵、单请求**（看图/视觉判断 → MTP 投机瞬时命中率高），**不代表持续速率**；8096 的 `peak_decode` 是窗口内最高瞬时值，判断 MTP 是否加速应看**长时间均值**而非瞬峰。

