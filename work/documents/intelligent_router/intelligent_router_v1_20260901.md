# 智能路由主题文档（第一部分：本地模型服务部署）

> 版本：v1 | 保存时间：2026-09-01 16:45（北京时间）
> 主题：signLanguage 团队"智能路由"（codex-deepseek-proxy :11435 综合代理）的本地模型服务部署、弹性池机制、关键 bug 修复与运维红线。
> 维护：顾问 / 运维（signL8）协作；本文为智能路由主题文档**第一部分**（本地模型服务部署），后续部分（如 DeepSeek/GPT 路由、tool-call 兼容层、质检等）另文。

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

## 7. 引用／关联

- 35B 部署：`work/documents/local_model_eval/local_model_qwen36_35b_a3b_deploy_v1_20260831.md`
- 弹性槽位事故报告：`work/documents/zhuhai_qwen3_8_27b_deploy/elastic_slot_stale_incident_report_20260829_v1.md`
- 代理隔离目录：`work/documents/zhuhai_qwen3_8_27b_deploy/codex-deepseek-proxy_isolated_20260825/`
- tool-call 兼容报告：`work/documents/advisor_toolcall_compat_report_20260831_v1.md`
- 代理变更记录：`~/.qwen/settings_fix_gpt_models_20260731.md`（2026-09-01 段：代理 finish 防护 + g29 max_tokens）
