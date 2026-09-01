# 智能路由主题文档（第一部分：本地模型服务部署）

> 版本：v1 | 保存时间：2026-09-01 16:45（北京时间）
> 主题：signLanguage 团队"智能路由"（codex-deepseek-proxy :11435 综合代理）的本地模型服务部署、弹性池机制、关键 bug 修复与运维红线。
> 维护：顾问 / 运维（signL8）协作；本文为智能路由主题文档**第一部分**（本地模型服务部署），后续部分（如 DeepSeek/GPT 路由、tool-call 兼容层、质检等）另文。

> **本文件模型简称对照（2026-09-01）**：
> - **27b** = **Qwen3.8-27B**（`qwen3.8-27b-int4-tp2-*`，g29/34/56/78 槽位；**稠密 27B，AWQ-INT4**）
> - **35b** = **Qwen3.6-35B-A3B**（`qwen3.6-35b-a3b-tp2-*`；**MoE，AWQ-4bit**，窗口 225280）
> - 全文（除模型 id 本身外）出现"27b/35b"均指以上两款；涉及对比类结论必写全型号（见 §7）。

---

## 1. 整体架构（nature 本机 ↔ zhuhai 服务器）

```
[客户端/Qwen Code 成员会话]
        │  OpenAI 兼容请求
        ▼
  nature 本机 :11435  codex-deepseek-proxy（智能路由，即"综合代理"）
        │  route（按 model 名选后端）
        ├──> GPT 官方（ChatGPT Codex backend via device-code OAuth）
        ├──> DeepSeek 官方（deepseek-v4-pro / flash）
        └──> 本地模型（vLLM 弹性池，SSH 隧道转发到 zhuhai）
                 │  ssh -N 隧道（18050/18053/18070 … → zhuhai 80xx）
                 ▼
  zhuhai 服务器  vLLM（AWQ-INT4 弹性池，GPU2-9 按需拉起）
```

- **统一入口**：`127.0.0.1:11435`（codex-deepseek-proxy，`src/main.py`，systemd user service `codex-deepseek-proxy.service`）。**所有本地模型调用必须经 11435，禁止绕过直连 zhuhai 端口**。
- **模型部署位置**：所有本地模型（vLLM INT4 弹性池、llama.cpp 等）在 **zhuhai**，不在 nature 本机（nature 无 GPU，仅跑 Qwen Code 主进程 + 代理 + 工作目录）。

## 2. 本地模型服务布局（弹性池 vLLM INT4）

| 槽位 | GPU 对 | 目标端口(zhuhai) | 隧道(nature→zhuhai) | 模型 | 窗口 |
|------|--------|------------------|----------------------|------|------|
| g29 | 2,9 | 8050 | 18050 | qwen3.8-27b-awq-int4 | 131072 |
| g29-35b | 2,9 | 8070 | 18070 | qwen3.6-35b-a3b-awq-4bit | 225280 |
| g34 | 3,4 | 8051 | 18051 | qwen3.8-27b | 131072 |
| g56 | 5,6 | 8052 | 18052 | qwen3.8-27b / 35b | 131072 / 225280 |
| g78 | 7,8 | 8053 | 18053 | qwen3.8-27b | 131072 |

> 注：弹性池为**按需拉起**（请求时启动，`idle_ttl`（默认 3h）空闲后释放）。同一 GPU 对可先后/并跑不同模型（如 g29 卡组上的 27b=8050 与 35b=8070 可能共存或轮流），**端口是关键区分标识**。

### 端口/隧道规则（本次修复的依据）
- **每个槽位独占一个端口**（模型 id 不同、端口不同；GPU 对可能相同）。
- **端口是区分"该进程属于哪个槽位"的最可靠字段**——远比 GPU 对更精确（因同 GPU 对会跑不同模型）。
- SSH 隧道进程为 `ssh -N` 常驻（PID 存活数月）；**隧道断 ≠ 实例断**，实例状态看 zhuhai 端口 health。

## 3. 智能路由核心机制（codex-deepseek-proxy）

- **按需拉起**：`_elastic_ensure` 保证实例运行——health 通过直接复用；否则启动并等待就绪（vLLM 加载 ~1-3 分钟）。启动段用全局锁串行化（避免多实例并发 torch.compile 互卡）。
- **空闲释放**：`idle_ttl`（默认 3h）超时无人用则释放。
- **僵死自愈**：`_kill_stale_elastic_workers`（main.py 268 行起）——端口未监听但 GPU 有孤儿 vLLM worker → 按进程组 kill -9，释放显存后重试拉起（源于超长上下文打崩 API Server 后 worker 占显存的真实事故）。
- **事务/保活**：`_elastic_health` / `_elastic_last_active` / `_elastic_ready` 维护实例状态。

## 4. ⚠️ 关键 bug 与修复（2026-09-01，重大）

### 4.1 事故现象
- 使用卡2+9（35b）时出现 `Model stream ended without a finish reason. Connection error.`，打断本地服务。
- 排查：18xxx 实例 health 恢复 200（瞬时错误），但日志反复出现：
  ```
  [elastic] qwen3.8-27b-int4-tp2-g29 僵死自愈：PGID 1021461 CUDA_VISIBLE_DEVICES=2,9 == 目标GPU对['2','9']，命中待清
  ```

### 4.2 根因（已确诊，非推测）
- `_kill_stale_elastic_workers("qwen3.8-27b-int4-tp2-g29")` 检查 27b-g29 槽位（port 8050，已释放）。
- 端口 8050 未监听 → 按 **GPU 对 {2,9} 匹配 VLLM 进程组**。
- **但卡2+9 上跑的是 35b（PGID 1021461，port 8070）**，其 `CUDA_VISIBLE_DEVICES=2,9` 与目标 GPU 对一致 → **被误判为"27b 僵死"、反复"命中待清"、试图 `kill -9` 杀掉运行中的 35b**。
- 根因：**只按 GPU 对匹配，无法区分同 GPU 对上的不同模型实例**（27b=8050 / 35b=8070 共享 GPU2,9）。

### 4.3 修复（main.py：`_kill_stale_elastic_workers` 判定处）
- 在 GPU 对匹配基础上，**增加校验进程 cmdline 的 `--port == 本槽位端口`**（用 `re.search(rf"--port[ =]{port}(?!\d)", cmdline)`）。
- 效果：27b-g29 槽位（port 8050）只清理 `--port 8050` 的进程；`--port 8070` 的 35b 即使 GPU 对相同也**跳过（防误杀）**。
- 备份：`/home/wuyangcheng/codex-deepseek-proxy/src/main.py.bak_portcheck_20260901`。
- 已重启 11435 生效；单测 6/6 PASS（27b 槽查 35b → 跳过、查真 27b 垃圾 → 命中、`--port=NNNN` 等号形式、负向前瞻防 `80500`/`8070` 误匹配）。

### 4.4 联动修复（同一根因链，代理流式收尾）
- 上游 vLLM 断流（`http.client.IncompleteRead(0 bytes read)`）时，`_handle_local_backend`（main.py 2773 起）原样转发、不作收尾 → 客户端报 `Model stream ended without a finish reason`。
- **修复**：补 finish_reason 防护 4 处（初始化 `sent_finish/resp_id/created` + 透传检测 finish_reason + EOF 无 finish 补发合成 stop + 新增 `except IncompleteRead` 断流补发）。备份 `main.py.bak_finish_patch_20260901`。

## 5. 运维红线（附：本次强化）

- **vLLM 启动强制规范**（team_constraints §3）：必设 `CUDA_VISIBLE_DEVICES`（目标槽位卡对）、host 只绑 `127.0.0.1`、不动 GPU1/GPU0（GPU0 仅单卡报主管）、启动前报主管、`served_model_name` 与实际模型一致、停实例用 `elastic_stop_vllm.sh <port>` / 带端口精确 PID，**严禁 pkill 宽匹配**，仅用标准模板 `/tmp/elastic_start_vllm_tp2_param.sh`。
- **僵死自愈判定必须含端口校验（2026-09-01 新增）**：任何"按 GPU 对/卡组匹配进程"的自动化清理逻辑，必须**同时校验进程 `--port`＝目标槽位端口**，防止跨模型误杀同卡组其它实例。
- **智能路由 tool-call 兼容硬规则**（2026-08-31，顾问 live 终验）：候选模型进 agentic/coding 档前必须过 `work/scripts/tool_call_compat_probe.py`；仅 30B-A3B 用 `hermes` 解析、35B-A3B(35b/Qwen3.6) 用 `qwen3_xml` 即可。

## 6. 生成参数机制（max_tokens / ctx / thinking）

- `max_tokens` = 单次生成**输出最大长度上限**；**输入(prompt)上限 = ctx − max_tokens**。
- 35b：窗口 225280、`samplingParams.max_tokens=32768`（2026-09-01 设，位置按先例放 `samplingParams` 下）；27b 窗口 131072。
- **thinking 也计入 max_tokens**：`reasoning.effort=high` 下先输出思考 token 再输出回答，思考+回答 ≤ max_tokens。思考占满预算 → 回答截断（`finish_reason=length`），这是早期"回答一半截断"的原因之一（配合加大 max_tokens / 降 reasoning 缓解）。
- 多轮会话 context 累积，接近窗口时 Qwen Code 自动 compress。

## 7. 本地模型视觉能力实测比较（2026-09-01，顾问实测）

> 详细记录：`intelligent_router/local_vision_capacity_cmp_v1_20260901.md`
> 方法：**直接走 OpenAI 兼容 API**（`127.0.0.1:11435/v1/chat/completions`，绕过 Qwen Code 前端），同题同图、temperature=0。4 题：颜色/OCR/位置、计数+空间、柱状图读值、中文 OCR。

### 7.1 被测对象
- **Qwen3.6-35B-A3B（35b）**：`qwen3.6-35b-a3b-tp2-g29`（MoE，AWQ-4bit，卡2+9、端口 8070，**运行中**）
- **Qwen3.8-27B（27b）**：`qwen3.8-27b-int4-tp2-g34`（稠密 27B，AWQ-INT4，卡3+4、端口 8051，**空闲实例**）

### 7.2 结果速览

| 题 | 评估能力 | Qwen3.6-35B-A3B(35b) | Qwen3.8-27B(27b) |
|----|---------|-----|-----|
| fig1 | 颜色/左右位置/文字 OCR（QK42） | ✅ 全对 | ✅ 全对 |
| fig2 | 计数(6)+形状颜色+数量比较(3蓝圆>2黄三角)+空间(左下) | ✅ 全对 | ✅ 全对 |
| fig3 | 柱状图**数值读取**+高低排序（真值 A150/B300/C220/D380） | ❌ **空输出** | ⚠️ 有推理但**数值上偏**（读成 A≈200/B≈400/C≈300/D>400） |
| fig4 | 中文 OCR（手语智能评估系统 2026） | ✅ 全对 | ✅ 全对 |
| 无图对照 | 是否诚实拒答 | ✅ 诚实说看不到 | ✅ 诚实说看不到 |

### 7.3 关键结论
1. **两者都有原生视觉**（Qwen3.x GDN 视觉塔，与两个模型同架构），实测图像 token 确实进入（带图 prompt≈250-330 vs 纯文字 ~40），**非 visionBridge 桥接**。
2. **基础能力（颜色/位置/OCR/计数/空间）强且持平**：fig1/2/4 两模型全部答对。
3. **分水岭在"图表/精细数值读取"（fig3）**：
   - **Qwen3.6-35B-A3B(35b) 完全宕机**（给足 800 token 仍 0 输出、无读数无推理）；
   - **Qwen3.8-27B(27b) 有结构化推理**（think 内逐刻度/逐像素坐标推断、能判断高低趋势与排序）但**绝对数值上偏**（把 300 读成 400、150 读成 200）。
   - → 两者对**精确图表读数都不可靠**，但 27b 至少能给出"趋势+排序"，35b 直接无产出。
4. **风格差异**：35b 输出更直接简洁；27b 在需推理的视觉题上**先写长 think 草稿再答** → 正文易溢出被截断（与文本任务"思考超长"同源，非视觉特有）。
5. **⚠️ Qwen Code 前端注意**：`~/.qwen/settings.json` 中 **Qwen3.6-35B-A3B(35b) 模型注释为"工具调用可用"、未标"视觉可用"**；而 **Qwen3.8-27B(27b) 标了"视觉可用"**。→ 前端对 35b **可能不默认启用本地图像 pipeline（或走 visionBridge）**。本测试是绕过前端直打 API 才测到真实多模态能力。**成员若要在 Qwen Code 里用 35b 看图，需先确认前端是否将 35b 当作视觉模型处理。**

### 7.4 建议分工（结合实测）
- **看真实图片/图表/带数据图**：优先 **Qwen3.8-27B**（有推理趋势，读数需人工核对）；Qwen3.6-35B-A3B 仅适合**描述/OCR**，不适合**精确读图/读数**。
- **精确考据（图表数值、硬事实）**：仍走**联网核实**或 **deepseek-v4-flash-vision-exp（官方 API，顾问在用，1M ctx）**。
- **视觉作为 agentic 一环（需看图决策）**：用 Qwen3.8-27B 或官方 VL 更稳；Qwen3.6-35B-A3B 虽有工具调用但视觉读取弱。

## 8. 引用／关联

- 35B 部署：`work/documents/local_model_eval/local_model_qwen36_35b_a3b_deploy_v1_20260831.md`
- 弹性槽位事故报告：`work/documents/zhuhai_qwen3_8_27b_deploy/elastic_slot_stale_incident_report_20260829_v1.md`
- 代理隔离目录：`work/documents/zhuhai_qwen3_8_27b_deploy/codex-deepseek-proxy_isolated_20260825/`
- tool-call 兼容报告：`work/documents/advisor_toolcall_compat_report_20260831_v1.md`
- 代理变更记录：`~/.qwen/settings_fix_gpt_models_20260731.md`（2026-09-01 段：代理 finish 防护 + g29 max_tokens）
- 本地引擎思考强度控制调研（2026-09-01，effort 机制 vLLM vs llama.cpp）：`work/documents/intelligent_router/local_reasoning_effort_control_v1_20260901.md`
