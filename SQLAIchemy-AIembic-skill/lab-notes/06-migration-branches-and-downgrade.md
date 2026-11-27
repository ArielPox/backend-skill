# 实验 06 阶段笔记：迁移分支、合并与降级

## 环境与验收依据

项目目录为 D:\myskills\SQLAIchemy-AIembic-skill。VS Code 选择项目 .venv，打开脚本并点击运行 Python 文件。用户发送 1 表示操作完成且结果符合预期。下列完成状态依据用户确认；本次整理读取了脚本，没有重新执行数据库操作。

## 迁移关系

- 共同起点 ba0b8f64f297。
- 分支甲 47ab6a8e1bae 添加可空的 projects.description，类型 Text。
- 分支乙 69c933827e00 添加可空的 devices.location，类型 String(100)。
- 合并版本 c5441c214269 的 down_revision 同时引用两个分支，upgrade 和 downgrade 都是 pass。

脚本的 heads 表示迁移文件末端。数据库当前版本记录实际执行到的位置。

## 操作顺序与已确认结果

| 脚本 | 操作及验收结果 |
|---|---|
| c10-check_migration_state.py | 起始脚本末端与数据库版本均为 ba0b8f64f297 |
| c11-create_parallel_migrations.py | 生成两条同起点分支，head 数量为 2 |
| c12-merge_parallel_migrations.py | 合并后脚本只有一个 head |
| c13-upgrade_merged_migrations.py | 两列创建成功，数据库到达合并版本，项目和设备数量一致 |
| c15-check_merge_downgrade.py | 修复后只撤销合并版本，两列保留，数据库记录两个分支末端 |
| c13-upgrade_merged_migrations.py | 再次升级到合并版本，两个字段和记录数量符合预期 |
| c16-prepare_rollback_demo.py | 独立库 p29_lab_rollback_demo 通过完整迁移链升级到合并版本 |
| c17-seed_rollback_demo.py | 固定样本保存描述与位置，重新查询验证成功 |
| c18-downgrade_demo_columns.py | 实验库退到共同起点，两列删除，项目和设备记录保留 |
| c19-upgrade_demo_verify_values.py | 再次升级后两列创建，样本原值均为 None |

以上均由用户发送 1 确认通过。c14-downgrade_merge_only.py 是早期同类脚本，本轮采用已修复的 c15。创建分支和合并脚本具有起点检查，复做时需先确认版本状态。

## 关键参数

创建第二条分支时，command.revision 的 head 指向 ba0b8f64f297，splice=True 允许从已有后续版本的起点分叉。

command.merge 的 revisions=("47ab6a8e1bae", "69c933827e00") 明确指定合并对象。合并文件的 down_revision 保存两个前置版本。

升级使用 command.upgrade(config, "head")。本课仅撤销合并节点使用 command.downgrade(config, "47ab6a8e1bae")。

c16、c18、c19 使用 sys.executable 启动 Alembic 子进程，cwd 设置为项目目录，子进程 DATABASE_URL 指向独立实验库。settings.py 的 override=False 使该环境变量优先。

## 实际报错与修复

截图关键错误为 alembic.util.exc.CommandError: Ambiguous walk。

此前使用 command.downgrade(config, "-1")。合并节点具有两个前置版本，本地 Alembic 解析相对后退目标时产生歧义，失败发生在构造降级计划的环节。

修复为 command.downgrade(config, "47ab6a8e1bae")。先用本地 Alembic 计算计划，确认仅撤销 c5441c214269。用户执行后确认数据库版本为 47ab6a8e1bae 和 69c933827e00，两个字段保留。

## 字段删除与再次升级对照

实验库 p29_lab_rollback_demo。项目编码 ROLLBACK-DEMO，设备编码 sensor-demo。

| 时点 | 项目描述 | 设备位置 | 样本记录 |
|---|---|---|---|
| c17 写入后 | 用于验证降级后的数据恢复 | 实验室 A 区 | 存在 |
| c18 降级后 | 列已删除 | 列已删除 | 存在 |
| c19 再升级后 | NULL，Python 读取为 None | NULL，Python 读取为 None | 存在 |

字段分支的 downgrade 包含 drop_column，upgrade 包含新增列定义。重新创建可空且无默认值的列后，已有行的新列值为 NULL。恢复原值需要备份或可信来源。

c17 会重新写入样本值。在 c18、c19 的对照中直接查询结果，才能观察迁移本身产生的值。

## 自测

只撤销合并节点，两个字段是否删除？用户回答保留，正确。准确函数名为 downgrade，实际撤销操作由降级路径中的函数内容决定。

删除字段后再次升级能否恢复原值？已通过实验确认字段重新创建、原值丢失。

## 从单个分支升级到合并版本

在项目目录的 VS Code 中依次运行 c20-upgrade_from_branch_a.py 和 c21-upgrade_from_branch_b.py。两个脚本分别使用 p29_lab_branch_a_demo 与 p29_lab_branch_b_demo。

| 实验 | 中间状态 | 升级到 head 的结果 |
|---|---|---|
| c20 先执行甲分支 | description 存在，location 缺失 | 补齐乙分支，再到 c5441c214269 |
| c21 先执行乙分支 | location 存在，description 缺失 | 补齐甲分支，再到 c5441c214269 |

两项均由用户发送 1 确认通过。结合 c16，已验证空库、甲分支、乙分支三种起点均可到达合并版本。

## 重复列冲突与事务边界

运行 c22-check_migration_conflict.py，使用 p29_lab_rollback_demo 中的 lab_migration_conflict 实验表。脚本每次重建这张专用表。

- 甲事务创建 location 并写入“实验室 A 区”，然后提交。
- 乙事务先添加 branch_b_marker，再尝试添加同名 location。
- 第二次加列触发 PostgreSQL 42701 重复列错误，乙事务回滚。
- 验收确认甲的列和值保留，乙的标记列消失。用户发送 1 确认通过。

这项实验使用独立表的 SQL 模拟迁移操作。实际创建冲突的 Alembic 分支及解决冲突后的升级链尚未演练。

自测中用户最初将失败原因解释为破坏事务原子性。纠正后的结论是同名列冲突导致失败，原子性决定失败事务中的修改一起撤销。用户随后正确回答甲已提交，乙的回滚只影响乙当前未提交的事务。

## 旧字段读写兼容与应用回退

运行 c23-check_old_app_compatibility.py，连接 p29_lab_rollback_demo。每次创建独立项目编码，显式使用原有字段写入项目和设备并提交，再查询原有字段及新增字段。

用户确认输出符合预期：

    旧应用写入成功，事务已提交
    旧应用查询成功
    项目描述：None
    设备位置：None
    最后上报时间：None
    数据库版本：['c5441c214269']
    旧字段读写兼容验收通过

此实验模拟旧字段 SQL 读写，覆盖本例可空新增字段的兼容性。完整旧应用版本的部署、接口与业务流程尚未进行实际回退验收。

发布判断自测中，用户最初提出先回退应用再回退数据库，并在删数据前备份。讨论后明确旧应用查询和写入正常时，可以保留新增字段及已有数据。新增字段允许为空，旧应用省略该字段即可写入；新应用需处理空值。

建议的实验发布顺序为添加兼容字段、验证旧字段读写、发布新应用、必要时回退应用并重新验收。如果需要删列降级，提前确定备份时间点、覆盖的数据及恢复验证方式。实际备份恢复仍待演练。

## 本阶段总结

- 迁移合并依赖明确的版本号，各条路径会补齐尚未执行的依赖。
- 降级效果由路径上的 downgrade 操作决定。
- 删除列会丢失该列数据，重新执行新增列迁移后，本例旧行对应值为 NULL。
- 重复列冲突需要修正迁移内容，事务回滚范围取决于事务边界。
- 应用回退与数据库降级分别判断，旧字段读写兼容时可保留新结构。

本轮课堂实验 c10 至 c23 已按用户反馈记录。完整旧应用部署回退、实际冲突迁移链修复和备份恢复尚未实操验证。
