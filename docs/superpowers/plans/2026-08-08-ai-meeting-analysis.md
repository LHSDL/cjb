# AI 会议分析实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用千问真实 API 为会议生成经过引用、日期和安全校验的摘要、决策与行动项建议。

**Architecture:** `ai` 包通过 `LLMClient` 隔离模型供应商，`AIAnalyzer` 依次执行 Prompt 构造、模型调用、Schema 与引用校验、日期转换、安全过滤和重复合并。结果只返回 CLI，不依赖行动项写服务。

**Tech Stack:** Python 3.11、OpenAI Python SDK、Pydantic 2、python-dotenv、Typer、Rich、pytest、阿里云百炼 Qwen

## Global Constraints

- 使用 `qwen3.7-plus-2026-05-26` 和百炼 OpenAI 兼容接口。
- API Key 只能来自 `DASHSCOPE_API_KEY`，不得输出或提交。
- 相对日期只以会议的 `meeting_date` 为基准。
- AI 输出只作建议，不写入正式行动项。
- 本阶段不实现人工确认闭环和评测。
- 所有业务代码遵循测试先行，所有 Git 提交使用中文。

---

### Task 1: AI 数据契约与 Prompt

**Files:**
- Modify: `pyproject.toml`
- Modify: `environment.yml`
- Create: `src/meeting_assistant/ai/__init__.py`
- Create: `src/meeting_assistant/ai/models.py`
- Create: `src/meeting_assistant/ai/prompts.py`
- Create: `tests/ai/test_models.py`
- Create: `tests/ai/test_prompts.py`

**Interfaces:**
- Produces: `RawAnalysis.model_validate_json(text)`
- Produces: `build_prompt(meeting) -> PromptRequest`

- [ ] 编写失败测试，要求 RawAnalysis 拒绝缺字段、额外字段和超过 20 条的结果。
- [ ] 编写失败测试，要求 Prompt 包含 JSON、安全规则、会议日期和行号化原文。
- [ ] 运行 `python -m pytest tests/ai/test_models.py tests/ai/test_prompts.py -v`，确认因模块缺失失败。
- [ ] 添加依赖、Pydantic 模型和 Prompt 构造器，输出 `PromptRequest(system, user, lines)`。
- [ ] 重新运行测试并提交：`定义AI输出契约与安全提示词`。

### Task 2: 引用、安全、日期与重复处理

**Files:**
- Create: `src/meeting_assistant/ai/security.py`
- Create: `src/meeting_assistant/ai/date_resolver.py`
- Create: `src/meeting_assistant/ai/validation.py`
- Create: `src/meeting_assistant/ai/deduplication.py`
- Create: `tests/ai/test_security.py`
- Create: `tests/ai/test_date_resolver.py`
- Create: `tests/ai/test_validation.py`
- Create: `tests/ai/test_deduplication.py`

**Interfaces:**
- Produces: `detect_injection(lines) -> list[SecurityWarning]`
- Produces: `resolve_date(expression, meeting_date) -> ResolvedDate`
- Produces: `validate_raw_analysis(raw, lines) -> None`
- Produces: `merge_duplicate_actions(actions) -> list[ActionSuggestion]`

- [ ] 分别为指定对抗文本、来源不存在、负责人无来源、“下周五”、模糊日期和重复合并编写失败测试。
- [ ] 实现最小检测、日期规则、逐字引用验证和确定性去重。
- [ ] 运行四个测试文件，确认全部通过。
- [ ] 提交：`实现AI结果校验与安全处理`。

### Task 3: 百炼客户端与分析编排

**Files:**
- Modify: `src/meeting_assistant/config.py`
- Create: `src/meeting_assistant/ai/client.py`
- Create: `src/meeting_assistant/ai/analyzer.py`
- Create: `tests/ai/test_client.py`
- Create: `tests/ai/test_analyzer.py`

**Interfaces:**
- Produces: `DashScopeSettings.from_env()`
- Produces: `LLMClient.complete(prompt) -> str`
- Produces: `DashScopeClient.complete(prompt) -> str`
- Produces: `AIAnalyzer.analyze(meeting) -> AIAnalysis`

- [ ] 用注入客户端编写分析成功、提示注入过滤、模型失败、不写行动项的失败测试。
- [ ] 为缺少配置、鉴权、超时和空响应编写客户端错误映射测试。
- [ ] 实现 `.env` 加载、OpenAI 兼容调用和分析流程。
- [ ] 运行客户端与分析器测试并提交：`接入千问模型并编排AI分析流程`。

### Task 4: CLI 与真实模型烟测

**Files:**
- Modify: `src/meeting_assistant/cli.py`
- Create: `tests/ai/test_ai_cli.py`
- Create: `tests/ai/test_dashscope_integration.py`

**Interfaces:**
- Produces: `meeting-assistant ai check-config`
- Produces: `meeting-assistant ai analyze ID [--json]`

- [ ] 编写失败测试，覆盖配置检查、Rich 输出、JSON 输出、错误退出和分析前后行动项数量不变。
- [ ] 实现 AI 命令组及展示。
- [ ] 使用任务书对抗输入执行一次真实模型烟测，只输出验证结论，不输出密钥。
- [ ] 提交：`完成AI分析命令与真实模型验证`。

### Task 5: 文档、全量验证与推送

**Files:**
- Modify: `README.md`
- Modify: `docs/design-and-collaboration.md`

- [ ] 更新环境变量、模型、Prompt、失败降级和演示步骤。
- [ ] 运行 `python -m pytest -v`、编译检查和 CLI 烟测。
- [ ] 检查 `.env` 被忽略且仓库中不存在密钥模式。
- [ ] 提交：`完善AI能力文档与验收说明`。
- [ ] 将中文提交推送到 `origin/master`。
