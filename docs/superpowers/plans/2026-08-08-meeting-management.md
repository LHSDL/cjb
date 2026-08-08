# 会议记录与行动项管理实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建可持久化、可测试的会议记录与手工行动项 Python CLI。

**Architecture:** CLI 负责交互，Service 负责业务规则，Repository 负责 SQLite。所有写操作经过 Service 和事务，第二阶段 AI 只能通过既有服务边界产生建议。

**Tech Stack:** Python 3.11+、Typer、Rich、sqlite3、pytest

## Global Constraints

- 所有 Git 提交说明必须使用中文。
- 会议日期必填，格式为 `YYYY-MM-DD`。
- 后续相对日期解析必须以会议日期为基准。
- 本阶段不实现 AI、Web、删除、人工确认闭环或评测。
- 每项行为遵循测试先行，测试必须先因缺少行为而失败，再进行最小实现。

---

### Task 1: 工程骨架与数据库

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/meeting_assistant/__init__.py`
- Create: `src/meeting_assistant/config.py`
- Create: `src/meeting_assistant/db.py`
- Create: `tests/conftest.py`
- Create: `tests/test_db.py`

**Interfaces:**
- Produces: `Database(path: Path)`, `Database.initialize()`, `Database.connect()`

- [ ] 编写数据库初始化失败测试，断言初始化后两张表、索引和外键约束存在。
- [ ] 运行 `python -m pytest tests/test_db.py -v`，确认因模块缺失失败。
- [ ] 添加项目配置、数据库连接和幂等建表实现。
- [ ] 重新运行测试，确认通过。
- [ ] 使用中文提交：`搭建项目骨架并初始化数据库`。

### Task 2: 会议管理

**Files:**
- Create: `src/meeting_assistant/models.py`
- Create: `src/meeting_assistant/validators.py`
- Create: `src/meeting_assistant/repositories.py`
- Create: `src/meeting_assistant/services.py`
- Create: `tests/test_meetings.py`

**Interfaces:**
- Produces: `MeetingService.create_meeting(title, meeting_type, meeting_date, record_text)`
- Produces: `MeetingService.list_meetings()`、`MeetingService.get_meeting(meeting_id)`

- [ ] 逐个编写会议创建、日期、空白、超长和查询测试，每次确认新测试先失败。
- [ ] 实现 `Meeting` 数据类、验证器、Repository 查询和 Service 业务规则。
- [ ] 每个行为实现后运行对应测试，再运行 `python -m pytest tests/test_db.py tests/test_meetings.py -v`。
- [ ] 使用中文提交：`实现会议记录管理`。

### Task 3: 行动项管理与筛选

**Files:**
- Modify: `src/meeting_assistant/models.py`
- Modify: `src/meeting_assistant/repositories.py`
- Modify: `src/meeting_assistant/services.py`
- Create: `tests/test_action_items.py`
- Create: `tests/test_filters.py`

**Interfaces:**
- Produces: `ActionItemService.create_action_item(meeting_id, content, owner, due_date)`
- Produces: `ActionItemService.update_action_item(action_id, content, owner, due_date)`
- Produces: `ActionItemService.complete_action_item(action_id)`
- Produces: `ActionItemService.list_action_items(owner=None, status=None, due_before=None, meeting_id=None)`

- [ ] 为新增、无效会议、编辑、完成、重复完成分别编写失败测试并实现最小行为。
- [ ] 为负责人、状态、截止日期和会议筛选分别编写失败测试并实现组合查询。
- [ ] 运行全部领域测试，确认通过。
- [ ] 使用中文提交：`实现行动项管理与筛选`。

### Task 4: CLI 与演示数据

**Files:**
- Create: `src/meeting_assistant/cli.py`
- Create: `src/meeting_assistant/seed.py`
- Create: `tests/test_cli.py`
- Create: `tests/test_seed.py`

**Interfaces:**
- Produces: `meeting-assistant` 命令入口
- Produces: `seed_demo(database)` 幂等写入 3 场会议、8 条行动项

- [ ] 为核心命令帮助、会议列表和演示数据幂等性编写失败测试。
- [ ] 实现 Typer 命令组、Rich 输出和幂等演示数据。
- [ ] 运行 CLI 与种子测试，确认通过。
- [ ] 使用中文提交：`完成命令行交互和演示数据`。

### Task 5: 可靠性、文档与最终验证

**Files:**
- Create: `README.md`
- Create: `docs/design-and-collaboration.md`
- Modify: tests as required by requirement coverage review

**Interfaces:**
- Produces: 从零安装、运行、生成样例和测试说明

- [ ] 对照任务书补齐异常和边界测试，确保不少于 6 个真实自动化测试。
- [ ] 编写 README 和设计协作说明，明确相对日期基准、风险、取舍和已知限制。
- [ ] 运行 `python -m pytest -v`、`python -m meeting_assistant.cli --help` 和演示数据烟测。
- [ ] 检查仓库中不存在密钥、数据库和缓存文件。
- [ ] 使用中文提交：`完善可靠性测试与项目文档`。
- [ ] 推送当前分支至 `origin` 并设置上游分支。
