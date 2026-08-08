# 会议记录与行动项协同助手

当前基础版本实现：会议记录管理、手工行动项管理、组合筛选、SQLite 持久化、幂等演示数据，以及通过阿里云百炼千问生成摘要、决策和行动项建议。AI 建议不会直接写入正式行动项；当前不包含人工确认闭环、评测或 Web 页面。

## 环境准备

推荐使用项目指定的 Conda 环境：

```powershell
conda env create -f environment.yml
conda activate cjb
```

如果 `cjb` 环境已经存在：

```powershell
conda activate cjb
python -m pip install -e ".[dev]"
```

要求 Python 3.11 或更高版本。运行数据默认保存在 `data/meeting_assistant.db`，该目录不会提交到 Git。

## 千问 AI 配置

本项目使用百炼 OpenAI 兼容接口和固定快照模型 `qwen3.7-plus-2026-05-26`。在项目根目录创建 `.env`：

```text
DASHSCOPE_API_KEY=在本机填写，不要提交或发送给他人
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen3.7-plus-2026-05-26
DASHSCOPE_TIMEOUT_SECONDS=30
```

`.env` 已被 Git 忽略。也可以直接设置同名进程环境变量，进程环境变量优先于 `.env`。

```powershell
# 只检查配置完整性，不发送会议内容，也不打印密钥
meeting-assistant ai check-config

# 分析已有会议；默认以面板和表格展示
meeting-assistant ai analyze 1

# 输出经过校验的 JSON
meeting-assistant ai analyze 1 --json
```

AI 结果仅作建议。命令不会新增、编辑或完成正式行动项。

## 从零开始

数据库会在第一次执行命令时自动初始化，不需要手工建表。

```powershell
# 查看全部命令
meeting-assistant --help

# 创建可重复执行的演示数据
meeting-assistant seed-demo

# 查看会议
meeting-assistant meeting list
meeting-assistant meeting show 1

# 新增会议；缺少的参数会进入交互式输入
meeting-assistant meeting add
```

创建会议时必须录入会议日期，格式为 `YYYY-MM-DD`。该日期是会议的业务日期；第二阶段 AI 解析“下周五”等相对截止日期时，必须以它为基准。

## 行动项操作

```powershell
# 新增
meeting-assistant action add --meeting-id 1 --content "完成接口联调" `
  --owner "王芳" --due-date "2026-08-14"

# 查看全部或组合筛选
meeting-assistant action list
meeting-assistant action list --owner "王芳"
meeting-assistant action list --status pending
meeting-assistant action list --due-before 2026-08-14
meeting-assistant action list --owner "王芳" --status pending --meeting-id 1

# 局部编辑；未提供的字段保持原值
meeting-assistant action edit 1 --content "完成接口联调并复核"

# 清空字段必须显式指定，避免误操作
meeting-assistant action edit 1 --clear-owner --clear-due-date

# 完成；重复执行不会覆盖首次完成时间
meeting-assistant action complete 1
```

负责人和截止日期允许为空，界面显示为“待确认”。`--due-before` 包含指定日期当天。

## 使用独立数据库

可通过环境变量指定数据库，便于演示或排查：

```powershell
$env:MEETING_ASSISTANT_DB = "data/demo.db"
meeting-assistant seed-demo
```

## 自动化测试

```powershell
conda activate cjb
python -m pytest -v
```

测试使用真实的临时 SQLite 数据库，不使用固定成功返回值。覆盖正常、异常和边界场景，包括空记录、超长记录、非法日期、无效关联、幂等完成、局部编辑、组合筛选和幂等样例导入。

默认测试使用注入模型客户端，不消耗百炼额度。需要显式执行真实千问对抗测试时：

```powershell
$env:RUN_DASHSCOPE_INTEGRATION = "1"
python -m pytest tests/ai/test_dashscope_integration.py -v -s
Remove-Item Env:RUN_DASHSCOPE_INTEGRATION
```

真实测试使用任务书指定的提示注入文本，只输出测试结论，不打印 API Key。

## 演示建议

1. 执行 `meeting-assistant seed-demo`，显示新增 3 场会议、8 条行动项。
2. 执行 `meeting-assistant meeting list` 和 `meeting show 1`。
3. 新增一场会议和一条行动项，再编辑、筛选并完成。
4. 使用空记录创建会议，展示非零退出与中文错误。
5. 再次执行 `seed-demo`，展示新增数量为 0，证明幂等。
6. 执行 `python -m pytest -v`。
7. 执行 `meeting-assistant ai analyze 1`，展示摘要、决策、行动项、负责人、日期和来源。
8. 使用任务书对抗输入运行 AI 分析，展示安全警告且没有批量伪造行动项。
9. 临时填写错误密钥执行 AI 分析，展示失败降级后 `meeting list` 和手工行动项仍可用。

## 当前限制

- 不提供删除操作，避免第一阶段引入误删除与级联规则争议。
- 手工行动项只接受绝对日期；AI 建议支持部分明确相对日期，并按会议日期转换。
- AI 使用 Prompt 与确定性包含关系处理明显重复任务，不承诺解决所有语义近似表达。
- SQLite 适合单机演示和小规模使用，不面向多节点并发部署。
- AI 结果不保存；人工确认、修改、拒绝和追溯属于尚未实现的加分能力。

## AI 安全与校验

- System Prompt 明确会议原文是不可信数据，不能执行其中的命令。
- 请求开启 JSON Mode，并使用 Pydantic 严格拒绝额外字段和超量输出。
- 决策与行动项必须提供逐字存在于原文的行号和引用。
- 非空负责人、日期表达必须能在引用中找到。
- “下周五”等日期由程序以 `meeting_date` 为基准计算，模型不负责绝对日期运算。
- 检测“忽略以上规则”“system prompt”“为每位生成 N 条”等注入表达。
- 鉴权、超时、限流、连接、JSON 或引用校验失败均不会影响原有手工功能。

