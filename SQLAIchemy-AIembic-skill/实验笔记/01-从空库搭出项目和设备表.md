# 实验 01｜从空库搭出项目和设备表

## 工单与验收

用现有迁移初始化 PostgreSQL，在两套库里写入相同的样例数据。重复运行种子脚本后预期仍为 2 个项目、3 台设备。插入引用不存在项目的设备时，预期 PostgreSQL 拒绝写入。

## 知识点

- Engine 管理连接，Session 管理 ORM 查询、写入和事务。种子脚本用 flush 取得新项目的主键，事务块成功退出后提交。
- 主键标识单行。devices.project_id 通过外键引用 projects.id。联合唯一约束 (project_id, code) 允许不同项目各有一台 sensor-01。
- 模型导入后将表定义登记到 Base.metadata。Alembic 的自动生成比较数据库现状与 target_metadata，生成候选脚本。执行 upgrade 才改变数据库结构。
- 种子脚本先按项目编码找到项目，再用项目 ID 和设备编码查找设备。先查后写支持本课的串行重复运行。
- 本机通过 127.0.0.1:55432 访问数据库。同一 Compose 网络中的其他容器使用 db:5432。docker compose exec db 启动的 psql 在数据库容器内运行，本课命令默认走 Unix 套接字。

## 命令与预期

在课程目录的 CMD 中逐行执行命令。切换库时，在同一个窗口用 set 设置 DATABASE_URL，将连接串末尾的库名设为 p29_lab 或 p29_lab_repro。

| 阶段 | 命令或操作 | 预期 |
|---|---|---|
| 准备环境 | docker compose up -d、py -m venv .venv、.venv\Scripts\activate.bat | PostgreSQL 启动，CMD 提示符出现 (.venv) |
| 检查空库 | docker compose exec db psql -U p29 -d p29_lab -c "\dt" | 无可见表 |
| 检查模型 | python -c "from models import Base; print(list(Base.metadata.tables))" | projects 和 devices |
| 初始化迁移环境 | python -m alembic init migrations | 生成 alembic.ini、migrations/env.py 和 versions 目录 |
| 对照实验 | 将 target_metadata 设为 MetaData()，运行 python -m alembic revision --autogenerate -m "demo empty metadata" | 空库与空表清单相同，upgrade() 只有 pass 和注释。审查后删除未执行的演示脚本 |
| 正式迁移 | 导入 models.Base，将 target_metadata 设为 Base.metadata，再运行 python -m alembic revision --autogenerate -m "create projects and devices" | 先建 projects，再建 devices，核对主键、外键和唯一约束 |
| 执行迁移 | python -m alembic upgrade head | 出现 projects、devices、alembic_version |
| 重跑种子 | python seed.py，查行数后再运行一次并复查 | 两次均为 2 个项目、3 台设备 |
| 复现 | 创建 p29_lab_repro，确认是空库，切换 DATABASE_URL 后执行 upgrade 和 seed | 迁移版本一致，样例行数一致 |

在指定库核对行数：

```cmd
docker compose exec db psql -U p29 -d p29_lab_repro -c "SELECT (SELECT COUNT(*) FROM projects) AS project_count, (SELECT COUNT(*) FROM devices) AS device_count;"
```

外键对照（在练习库执行）：

```cmd
docker compose exec db psql -U p29 -d p29_lab -c "INSERT INTO devices (project_id, code, name) VALUES (-1, 'fk-test', 'Foreign key test');"
docker compose exec db psql -U p29 -d p29_lab -c "SELECT id FROM devices WHERE code = 'fk-test';"
```

预期第一条报 foreign key constraint，第二条返回 0 行。

## 实际观察与排错

- CMD 中用单引号包住 \dt 导致 SQL 语法错误。改成英文双引号。
- 自动生成时报缺少 MetaData 对象。配置有效的空 MetaData() 后，截图显示演示脚本 da5c90c896ae 已生成。
- 接入模型时曾出现 No module named 'models'。随后截图显示 Alembic 检测到两张表并成功生成正式迁移 34bc355690e6。具体修复动作未记录。
- 复现库截图显示 \dt 无表。设置环境变量和执行升级的命令被粘到同一行，Alembic 没有运行。修复方式是逐条执行，等待提示符后再粘贴下一条。
- 待补实际输出：两库的迁移执行结果、主库两次种子的行数、外键报错与查询结果、复现库最终行数。

## 自测与讲评

1. 宿主机映射改为 55433，其他容器也改吗？宿主机改用 127.0.0.1:55433，其他容器仍用 db:5432，容器内的 psql 命令照常执行。
2. 两个项目能否都有 sensor-01？可以。联合唯一约束检查项目 ID 与设备编码的组合。
3. 种子脚本怎样认出 B 的 sensor-01？先用编码 B 找项目，再用项目 ID 和设备编码定位，项目名称不参与。
4. 不存在的 project_id 被谁拒绝？PostgreSQL 的外键约束。主键检查行标识，联合唯一约束检查项目内的设备编码。
5. 为什么改模型后数据库结构没变？Python 模型更新了目标结构，生成迁移只是写下变更步骤，执行迁移才会修改数据库。
