# 实验 05 阶段笔记：设备最后上报时间与分批回填

记录日期为 2026-11-20。本文件记录当前阶段，完整课程验收仍有待完成的项目。

## 环境与运行方式

项目目录为 D:\myskills\SQLAIchemy-AIembic-skill。Python 脚本在 VS Code 中选择项目 .venv\Scripts\python.exe 后，点击“运行 Python 文件”。settings.py 加载项目 local.env 中的 DATABASE_URL。

## 目标与业务规则

- 给有历史数据的 devices 表增加 last_seen_at。
- 没有可信上报记录的设备保留 NULL，Python 读取为 None。
- 同一设备的来源记录取最大上报时间。
- 目标为空或来源时间更晚时更新，相同或更早时跳过。
- 每批独立提交。失败批次回滚，已经提交的批次保留。
- 重跑时重新检查所有输入，跳过已完成的相同数据。

本实验使用人工构造的 UTC 上报时间和设备 ID 1、2。生产回填需要使用实际设备上报来源。

## 结构迁移

已读取模型，Device.last_seen_at 定义为可空的带时区时间。

已读取迁移文件 migrations/versions/ba0b8f64f297_add_device_last_seen_at.py。

- 上一版本为 56e4a4beeaad。
- 新版本为 ba0b8f64f297。
- upgrade 添加 devices.last_seen_at，nullable=True，无默认值。
- downgrade 删除该列，执行降级会删除这一列已经保存的数据。

复做时在项目目录的 VS Code 集成终端执行下列命令。现有项目已经有该迁移文件，直接使用现有文件升级。

	python -m alembic upgrade head
	python -m alembic current

首次生成该迁移时使用的命令为下面这一条。

	python -m alembic revision --autogenerate -m "add device last_seen_at"

生成后检查 upgrade 中只有预期的新增列操作，再执行升级。

## 实际遇到的报错

### Python 模型缺少属性

报错为 AttributeError: 'Device' object has no attribute 'last_seen_at'。

检查 Device 类中的字段定义，保存 models.py，重新运行脚本。后续用户提供的模型列清单已包含 last_seen_at。

### 数据库缺少列

报错为 ERROR: column d.last_seen_at does not exist。

用户在迁移目录搜索 last_seen_at 时没有输出。当时模型已经有字段，对应迁移尚未生成。随后生成并应用新增列迁移。当前文件检查已找到 ba0b8f64f297，用户后续查询脚本成功读取两台设备的 None 值。

## 实验顺序与预期

1. c5-check_optional_last_seen.py 使用原有导入函数创建项目和设备，检查新字段为 None。这项测试覆盖当前代码中的原有导入函数，完整旧应用版本的冒烟测试仍待验证。
2. c7-preview_last_seen_backfill.py 取前两台设备，按设备汇总模拟记录中的最大时间。
3. 初次回填预期更新 2 台，再次运行预期更新 0 台。
4. 来源改成较早时间，预期更新 0 台，原有值保留。
5. 设备 1 来源改成 2026-01-05 12:00 UTC，设备 2 继续使用较早记录，预期更新 1 台；再跑更新 0 台。
6. 分批脚本使用 2026-01-07 的记录，每批一台，初次各更新 1 台，再跑各更新 0 台。
7. 将来源改成 2026-01-08，第二批 UPDATE 后人为抛出 RuntimeError。第一批提交，第二批回滚。
8. 删除故障注入，将最终断言改为两台设备都达到来源时间。重跑预期第一批更新 0 台、第二批更新 1 台。
9. 再次运行最终脚本，预期两批都更新 0 台。

## 关键代码位置

- models.py 定义字段及其可空性。
- migrations/versions/ba0b8f64f297_add_device_last_seen_at.py 定义结构变更。
- c7-preview_last_seen_backfill.py 演练来源汇总与单事务回填。
- c8-backfill_last_seen_batches.py 演练分批提交、故障和重跑。

最终分批脚本将以下条件放入 UPDATE 的 WHERE 中。

	Device.id == device_id
	or_(Device.last_seen_at.is_(None), Device.last_seen_at < reported_at)

每次循环使用 with Session(engine) as session, session.begin()。提交成功消息在事务块外打印。当前脚本捕获 RuntimeError，用于演示人为故障；数据库驱动异常仍会向外抛出，事务上下文退出时处理回滚。

故障注入位置是 UPDATE 执行之后、退出事务块之前。

	if batch_number == 2:
	    raise RuntimeError("模拟第二批处理失败")

复做失败对照需要让第二批来源晚于当前值，再注入异常，才能观察真实更新被撤销的效果。

## 已获得的实际证据

用户贴出的预览输出包括下面内容。

	设备 ID：1，编码：sensor-01
	当前时间：None
	来源最新时间：2026-01-05 10:00:00+00:00
	设备 ID：2，编码：sensor-02
	当前时间：None

设备 2 的来源时间未包含在该段输出中。

2026-11-20 已读取最终分批脚本。故障注入已删除，最终断言要求两台设备均达到来源时间。来源时间分别为 2026-01-08 10:00 UTC 和 2026-01-08 11:00 UTC。

其余操作后的“1”按继续教学处理。当前尚未收到各批提交数量、失败回滚和重跑的实际输出，以上对应数量保留为预期。此次整理没有执行数据库脚本。

## 自测与回答

- 当前为 10:00，来源为 12:00，应更新。用户回答正确。
- 回填成功后再次运行，相同数据更新数量为 0。用户回答正确。
- 缺少上报记录时保留 NULL。用户回答正确。

## 后续验收

- 收集最终脚本重复运行时两批更新数量及查询结果。
- 核对升级前后行数、Alembic 实际版本以及新应用对未知时间的输出。
- 完成旧应用版本的兼容性验证。
- 独立必填字段的临时表实验已写入 c9-check_required_column.py，实际输出待收集。课程计划中的隔离数据库副本与迁移版本失败检查仍待进行。last_seen_at 保持可空。

## 独立必填字段的失败与修复实验

已读取 c9-check_required_column.py，确认包含下列完整流程。该实验使用事务结束时清理的临时表 lab_devices，登记来源字段为 registration_source。约定两条模拟记录均来自旧系统导入。

1. 创建临时表，插入 sensor-01 和 sensor-02。
2. 在保存点内直接添加 TEXT NOT NULL 列，预期得到 SQLSTATE 23502。
3. 撤销保存点内失败操作后，检查原有两条记录。
4. 添加可空列，将已有记录来源回填为 legacy_import。
5. 查询剩余空值，要求为 0，再执行 SET NOT NULL。
6. 在保存点内尝试插入来源为 NULL 的第三条记录，预期再次得到 23502，验证约束执行。

在 VS Code 中选择项目 .venv，打开 c9-check_required_column.py，点击运行 Python 文件。预期末尾输出为“写入空来源被拒绝，非空约束验收通过”。尚未收到该输出，脚本内容检查已经完成。本次整理没有运行脚本或查询数据库。

该实验把全部动作放在一个外层事务中。实际分阶段发布还需要在收紧约束前，确保应用写入逻辑已经提供登记来源。

## 用户确认补记

2026-11-20，用户明确约定发送 `1` 表示当前运行结果与给出的预期一致。非空列失败对照、回填、设置非空约束和再次写入 NULL 被拒绝，已由用户按此约定确认通过。前文“实际输出待收集”等表述保留了当时记录状态，此项实验以本次用户确认为准。
