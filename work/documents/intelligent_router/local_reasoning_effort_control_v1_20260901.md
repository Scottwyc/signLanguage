# 本地推理引擎思考强度控制（effort）调研与技术文档

> 版本：v1 | 保存时间：2026-09-01 21:20（北京时间）
> 执行：顾问（本会话）| 目标：回答「我们本地 vLLM/llama.cpp 能否像官方一样控制思考强度( reasoning_effort )」
> 结论先行：**能，但要看引擎**。vLLM 0.19 对 Qwen3 不生效；llama.cpp 0.3.0 完整支持 reasoning_effort（经 chat template 把 effort 转成推理指令注入 system 提示词），但/是**提示词引导而非硬限制**。

---

## 1. 背景与问题

用户观察到：**本地 AWQ4 量化的 Qwen3.6-35B-A3B（35b）思考过长 → 截断 / 1 turn 停 / think 折叠失败**。最初尝试改 Qwen Code `settings.json` 的 `reasoning.effort: high→medium`，但实测发现**对本地 vLLM 无效**。用户进一步追问：「官方模型部署为什么就能 /effort 改思考强度？我们本地 vLLM 或 llama.cpp 难道就不能像官方一样控制 effort 吗？」

本文档回答：**我们自部署引擎也能控制思考强度，但机制、参数、前提各异**，且跟官方（云端）不同（官方是供应商引擎原生实现；本地引擎需依赖模板/参数实现）。

---

## 2. 关键区分：官方模型 vs 本地模型（baseUrl 决定一切）

我们的 Qwen Code settings 里模型分两类，**baseUrl 决定运行引擎**：

| 模型类别 | baseUrl | 实际运行引擎 | /effort 效力 |
|---------|---------|------------|------------|
| 官方 Qwen（qwen3.6-plus/qwen-max/qwen3.5-plus） | `https://dashscope.aliyuncs.com/compatible-mode/v1` | **阿里云百炼 DashScope 云端服务**（供应商自家推理栈） | ✅ 有效 |
| 官方 DeepSeek（deepseek-v4-flash） | `https://api.deepseek.com` | **DeepSeek 官方云端 API** | ✅ 有效 |
| 本地 27b/35b（qwen3.8-27b/qwen3.6-35b-a3b） | `http://127.0.0.1:11435/v1` | **我们 zhuhai 的 vLLM 0.19** | ❌ 对 Qwen3 无效 |

**核心**：官方模型是**只调 API、不部署**，effort 由**供应商引擎**原生实现；本地模型是**我们自己部署**，effort 能否生效取决于**我们用的引擎是否实现了它**。

---

## 3. vLLM 0.19：对 Qwen3 的 reasoning_effort 无效（源码+实测确认）

### 3.1 实测证据
| 模型 | 中性/medium/high completion | 结论 |
|------|------------------------------|------|
| Qwen3.8-27B（int4-tp2-g78） | 81 / 97 / 80 | 波动随机级，**无效** |
| Qwen3.6-35B-A3B（int4-tp2-g29） | 859 / 792（medium）, 波动<8% | 思考长度无实质变化，**无效** |
| 裸测 35b completion≈1300 但正文仅 60 字 | 思考占 ~95% token | 截断/1 turn 停根因 |

### 3.2 源码证据（zhuhai vLLM 0.19）
- `--reasoning-parser qwen3`：**只做输出解析**（拆 `<think>`/`</think>` 为 reasoning/content），**不控制思考长度**。
- vLLM 服务端**无 `--reasoning-effort` 参数**（`--help` 无此项）。
- 协议层 `reasoning_effort` 字段（`chat_completion/protocol.py:182`）**仅对 Harmony/GPT-OSS 模型生效**（`harmony_utils.py` 的 `REASONING_EFFORT` 映射，经系统提示词注入）；**对 Qwen3 无作用**。
- `--reasoning-config` 只配置 `<think>`/`</think>` 解析边界（`config/reasoning.py`），**不控制思考长度**。

### 3.3 结论
vLLM 0.19 对 Qwen3 系列（27b/35b）的 `reasoning_effort` **无效**。它只对 Harmony/GPT-OSS 模型实现了 effort→提示词注入。

---

## 4. llama.cpp 0.3.0：完整支持 reasoning_effort（实测有效）

### 4.1 源码证据
llama.cpp 0.3.0 **原生支持 reasoning_effort**：
- **命令行**：`--reasoning-effort LEVEL`（`minimal/low/medium/high/xhigh/max`，`common/arg.cpp:3669-3676`）
- **请求级**：OpenAI 兼容 `inp["reasoning_effort"]` → `caps_apply_reasoning_effort`（`common/chat.cpp:970-972`）
- **模板变量**：设 `reasoning_effort` + `reasoning_strength` 两个 Jinja 变量（`common/jinja/caps.cpp:29-31`）
- **`--reasoning-format deepseek`**：把思考提取到 `message.reasoning_content`

### 4.2 实测证据（Qwen3.8-27B-UD-Q4_K_M，单卡 GPU5）
高难度逻辑题（三箱钻石），max_tokens=4000：

| effort | reasoning_len | content_len | completion | 耗时 |
|--------|--------------|------------|-----------|------|
| low | **7533** | 877 | 2810 | 96s |
| medium | 5970 | 935 | 2228 | 76s |
| high | 3525 | 406 | 1385 | 48s |
| 默认 | 4722 | 681 | 1911 | — |

> ⚠️ **反直觉**：expected low=最短，但实测 low 最长、high 最短（与官方"high=多想"语义相反）。原因见 §4.3。

### 4.3 控制机制（决定性发现）
Qwen3.8-27B 的 GGUF 内嵌 chat template **确实引用 `reasoning_effort`**，但控制方式是**把 effort 翻译成一段推理指令注入 system 提示词**（`reasoning_instructions`）：

```jinja
{%- set resolved_reasoning_effort = reasoning_effort|default('xhigh') %}
{%- if resolved_reasoning_effort not in ('xhigh','medium','low') %}
    {{- raise_exception('Unexpected reasoning effort ...') }}
{%- endif %}
{%- if resolved_reasoning_effort == 'xhigh' %}
    {%- set reasoning_instructions = 'Reasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, prioritize correctness...' %}
{%- elif resolved_reasoning_effort == 'low' %}
    {%- set reasoning_instructions = 'Reasoning effort is set to low. Keep your thinking brief and focused, moving directly to the conclusion...' %}
{%- endif %}
```

**关键**：
- effort 被**翻译成 system 提示词指令**（xhigh=多想、low=少想），**非硬性 token 上限**。
- `high` 会被归一成 `xhigh`（`resolved_reasoning_effort='high' → 'xhigh'`）。
- **效果依赖模型对指令的遵循度**——不是精确控制思考 token 数。
- **实测方向反**（low 反而最长）说明：指令引导未必能被模型稳定遵循，或测试在同一 slot 缓存下受模型随机性干扰；结论是「llama.cpp 支持 effort，但它是**提示词引导级**控制，非确定性强限制」。

---

## 5. 为什么 llama.cpp 能、vLLM 对 Qwen3 不能

| | llama.cpp 0.3.0 | vLLM 0.19 |
|---|---|---|
| reasoning_effort 参数 | ✅ 有（CLI + 请求级） | ⚠️ 协议层有，但仅 Harmony/GPT-OSS 用 |
| 控制机制 | 把 effort 注入 chat template → 转 system 提示词指令 | effort 仅对 Harmony 转提示词；Qwen3 忽略 |
| 对 Qwen3 生效 | ✅（模板消费 reasoning_effort 变量） | ❌（Qwen3 parser 不消费 effort） |
| 控制精度 | **提示词引导级**（非硬限制） | — |
| 硬性限制思考 token | ❌ 无（仅 enable_thinking 开关） | ✅ 可用 `thinking_token_budget`（但需 `--reasoning-config` 解锁） |

**一句话**：llama.cpp 把 effort 当「会传给模型的模板参数」，靠模板转提示词引导；vLLM 0.19 把 effort 只视为「Harmony 模型的特性」，对 Qwen3 直接忽略。

---

## 6. 若真要「硬性」限制本地模型思考长度

### 6.1 vLLM：`thinking_token_budget`（硬限制，源码级确认）
- vLLM 0.19 协议层 `thinking_token_budget`（`chat_completion/protocol.py:183`）→ `sampling_params.thinking_token_budget`（`sampling_params.py:288`）→ **logits processor**（`v1/sample/logits_processor/builtin.py:352-498`）：解码时计数 `<think>` token，达预算**强制 `</think>` 进正文**。
- **门控**：需启动加 `--reasoning-config '{"reasoning_start_str":"<think>","reasoning_end_str":"</think>"}'` 解锁（否则报 `thinking_token_budget is set but reasoning_config is not configured`）。`--reasoning-config` 接收 `json.loads` JSON（`arg_utils.py:336`）。
- 字段**能从 11435 透传**到 vLLM（发 `thinking_token_budget=0` 返回门控报错，链路通）。
- **Status**：已确认可行，但需改 zhuhai 35b 启动脚本 + 重启实例（Owner 决定暂不落地）。

### 6.2 llama.cpp：`enable_thinking`（开关）+ 模板引导
- `enable_thinking=False` 彻底关思考（实测 35b 用它 completion 从 800→27，立竿见影）。
- reasoning_effort 是**软引导**（转提示词指令），非硬限制。

---

## 7. 结论 & 建议

1. **本地引擎能控制思考强度**，但要选对引擎/参数：
   - **llama.cpp**：支持 `reasoning_effort`（CLI/请求级），但**经模板转提示词**，是软引导，效果依赖模型遵循度，且实测方向反（xhigh 语义需实测校准）。
   - **vLLM 0.19**：对 Qwen3 的 effort **无效**；要**硬限制**需 `thinking_token_budget`（配 `--reasoning-config`）或 `enable_thinking` 开关。
2. **官方 vs 本地差异本质**：官方 = 供应商引擎原生实现；本地 = 我们部署的引擎，能否生效取决于引擎是否实现 + 模型模板是否消费。
3. **当前 35b 思考过长**：改 `reasoning.effort` 无效（vLLM 不吃）；真正有效是 vLLM 的 `thinking_token_budget`（硬限）或 `enable_thinking=False`（关思考）。已靠**死循环 watchdog** 自动打断兜底。
4. **后续选项**（未落地，按需）：
   - vLLM 35b 加 `--reasoning-config` + 请求传 `thinking_token_budget`（精确限思考）。
   - 若用 llama.cpp 跑模型，可试 `--reasoning-effort` 但需实测校准方向/效果。

---

## 8. 关联文件
- 实测脚本：`/tmp/test_35b_budget.py`、`/tmp/test_llama_effort_hard.py`（zhuhai `/tmp/`）
- vLLM 源码：`vllm/api/util`、`vllm/reasoning/qwen3_reasoning_parser.py`、`vllm/v1/sample/logits_processor/builtin.py`
- llama.cpp 源码：`common/jinja/caps.cpp`、`common/chat.cpp`、`common/arg.cpp`
- 智能路由主题文档：`intelligent_router_v1_20260901.md`
- 35b 思考控制记忆：项目记忆 `35b-thinking-control-reasoning-effort-ineffective`
