# 会议记录与行动项管理设计

## 目标与范围

第一阶段交付一个 Python 命令行应用，使用 SQLite 持久保存会议记录和手工行动项。用户可以新增会议、查看会议列表与详情，以及新增、编辑、完成和筛选行动项。本阶段不接入大模型，不实现 AI 确认闭环和评测。

工程必须独立可运行，并为第二阶段 AI 能力提供稳定接口。会议日期是必填字段；后续 AI 遇到“下周五”等相对截止日期时，必须以所属会议日期为基准转换为绝对日期，不能默认使用模型调用日期。

## 技术方案

- Python 3.11+
- Typer 提供命令行入口
- Rich 展示列表、详情和错误
- Python `sqlite3` 持久化数据
- pytest 运行自动化测试
- `src` 布局隔离应用代码与测试

应用采用 CLI、Service、Repository 三层结构。CLI 只处理输入输出；Service 承担校验和状态转换；Repository 封装 SQL 和事务。该边界允许第二阶段 AI 将解析结果交给 Service，而不直接修改数据库。

## 数据模型

### meetings

- `id`: 自增主键
- `title`: 必填，去除首尾空格后长度 1-100
- `meeting_type`: 必填，长度 1-50
- `meeting_date`: 必填，格式 `YYYY-MM-DD`
- `record_text`: 必填，去除首尾空格后长度 1-50000
- `created_at`、`updated_at`: UTC ISO 8601 时间

### action_items

- `id`: 自增主键
- `meeting_id`: 必填外键
- `content`: 必填，长度 1-500
- `owner`: 可空；空值表示待确认
- `due_date`: 可空；非空时格式为 `YYYY-MM-DD`
- `status`: `pending` 或 `completed`
- `completed_at`: 完成后记录 UTC 时间
- `created_at`、`updated_at`: UTC ISO 8601 时间

数据库启用外键约束、状态检查约束、忙等待超时，并为负责人、状态、截止日期和会议外键建立索引。

## 命令行接口

```text
meeting-assistant meeting add
meeting-assistant meeting list
meeting-assistant meeting show <MEETING_ID>
meeting-assistant action add --meeting-id <MEETING_ID>
meeting-assistant action edit <ACTION_ID>
meeting-assistant action complete <ACTION_ID>
meeting-assistant action list [--owner NAME] [--status STATUS] [--due-before DATE]
meeting-assistant seed-demo
```

新增和编辑命令使用交互式提示，避免长会议记录与中文内容的命令行转义问题。所有失败都返回非零退出码和中文错误信息。

## 需求假设

1. 会议日期是业务日期，不记录时区，使用 `YYYY-MM-DD`。
2. 第一阶段只接受绝对截止日期；相对日期由第二阶段 AI 以会议日期为基准解析。
3. 负责人和截止日期可以为空，以表达尚未明确。
4. 行动项初始状态为 `pending`；完成操作幂等，重复完成不覆盖首次完成时间。
5. 第一阶段不提供删除功能，避免误删除及级联规则争议。
6. 第一阶段不自动进行语义去重；重复行动项由用户手工编辑，第二阶段再增加 AI 建议去重。
7. 数据库默认位于 `data/meeting_assistant.db`，可通过环境变量 `MEETING_ASSISTANT_DB` 覆盖。

## 可靠性

识别并处理：空白输入、超长记录、非法日期、无效外键、重复完成、数据库锁定、数据库目录不可写、演示数据重复导入。写操作使用事务，业务校验与数据库约束双重防护，异常不会被吞掉。

## 测试与验收

测试使用真实临时 SQLite 数据库，覆盖会议创建和持久化、输入边界、行动项增改完成、幂等完成、三种筛选、无效会议关联和演示数据幂等。最终提供一键测试命令，并确保至少有 3 场会议和 8 条行动项的演示数据。
