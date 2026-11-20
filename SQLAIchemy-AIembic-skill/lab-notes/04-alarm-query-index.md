# 第四课：告警查询与复合索引

## 实际执行计划证据

- 无复合索引：Seq Scan 检查 26,000 行，保留 2,016 行，过滤 23,984 行。top-N heapsort 使用 32 KB，顶层 shared hit=225，Execution Time=1.882 ms。
- 有索引、带状态筛选：截图确认 ix_alarms_device_status_occurred_id 上的 Index Only Scan，Heap Fetches=0。截图不含完整总耗时。
- 查询增加 message：Index Scan 使用相同索引，返回 50 行，无独立 Sort，Execution Time=1.099 ms。
- 去掉状态条件：Index Only Scan 输出 10,080 行，Heap Fetches=0，再进行 top-N heapsort，使用 28 KB。Execution Time=3.368 ms。
- 重启及缓存状态不同，单次耗时不能用于量化索引带来的固定加速倍数。

## 原理与命令

索引顺序为 device_id、status、occurred_at DESC、id DESC。前两列等值确定后，可按时间和 ID 顺序读取。省略状态后，各状态组需要统一排序。索引增加存储和写入维护成本，应结合查询频率、实际计划和写入压力决定是否增加另一种索引。

在项目目录运行 `python -m alembic revision --autogenerate -m "add alarm query index"`，审查后执行 `python -m alembic upgrade head`。

用 `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` 取得计划。先运行 `ANALYZE alarms;` 更新统计信息。psql 加 `-P pager=off` 完整输出。

## 接口验收预期

GET /api/v1/devices/{device_id}/alarms 支持 start、end、可选 status，返回最新 50 条。

- [00:00Z, 00:01Z) 包含零点告警，相邻下一段包含 00:01Z 告警。
- +08:00 的 08:00 与 UTC 零点代表同一时刻。
- start >= end、缺少时区、非法状态返回 422。
- 不存在的设备返回 404；设备存在但无匹配告警返回 200 和空列表。
- 省略状态，00:00Z 到 00:03Z 的种子数据应包含两条 open 和一条 closed。

上述接口验收在教学中已安排，尚未收到实际响应截图或文本，保留为待核实项。

## 排错与自测

- DATABASE_URL 缺失：项目 local.env 经 settings.py 自动加载，已设置的环境变量优先。
- psycopg 缺失：VS Code 曾使用其他 Python，改用项目 .venv 解释器。
- db 未运行：docker compose up -d db，再用 pg_isready 验证。
- device_id 是 alarms 的外键，alarms.id 是告警主键。
- flush 后仍可事务回滚；Alembic downgrade 是执行迁移降级步骤；备份恢复负责恢复历史数据。
- message 不在索引中，查询它时需要取表数据，索引仍可用于定位和排序。
