# 会议记录与行动项协同助手

第一阶段实现：会议记录管理、手工行动项管理、组合筛选、SQLite 持久化和幂等演示数据。当前不包含 AI 提取、人工确认闭环、评测或 Web 页面。

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

## 演示建议

1. 执行 `meeting-assistant seed-demo`，显示新增 3 场会议、8 条行动项。
2. 执行 `meeting-assistant meeting list` 和 `meeting show 1`。
3. 新增一场会议和一条行动项，再编辑、筛选并完成。
4. 使用空记录创建会议，展示非零退出与中文错误。
5. 再次执行 `seed-demo`，展示新增数量为 0，证明幂等。
6. 执行 `python -m pytest -v`。

## 当前限制

- 不提供删除操作，避免第一阶段引入误删除与级联规则争议。
- 第一阶段只接受绝对日期；相对日期将在 AI 阶段按会议日期解析。
- 不自动进行语义重复判断；重复行动项当前由用户手工处理。
- SQLite 适合单机演示和小规模使用，不面向多节点并发部署。

