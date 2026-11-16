# 实操复习｜设备导入冲突、事务回滚与重试

在 Windows CMD 的 `D:\myskills\SQLAIchemy-AIembic-skill` 下操作。目标是制造设备编码冲突，查库验证整批回滚，再用同一项目编码修正重试。

## 1. 核对连接并启动 API

激活课程虚拟环境，在同一窗口设置 `DATABASE_URL`，目标为 Windows 侧的 `127.0.0.1:55432/p29_lab`。此前遇到 `getaddrinfo failed`，检查发现连接串没有解析出端口。重新设置时明确写入 `:55432`，密码使用本地配置。

```cmd
python -c "import os; from sqlalchemy.engine import make_url; u=make_url(os.environ['DATABASE_URL']); print(u.host, u.port, u.database)"
python -c "import os; from sqlalchemy import create_engine, text; c=create_engine(os.environ['DATABASE_URL']).connect(); print(c.scalar(text('SELECT current_database()'))); c.close()"
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

预期解析出 `127.0.0.1 55432 p29_lab`，实际连接查询输出 `p29_lab`。保持服务窗口开着，后续操作用第二个 CMD。

## 2. 发送重复设备编码

```cmd
curl.exe -i -X POST "http://127.0.0.1:8000/projects/import" -H "Content-Type: application/json" -d "{\"project_code\":\"REVIEW-ROLLBACK-01\",\"device_codes\":[\"sensor-01\",\"sensor-01\"]}"
```

截图确认返回 `409 Conflict`，正文提示 `Device codes must be unique within a project.`

## 3. 重试前查库

```cmd
docker compose exec db psql -U p29 -d p29_lab -P "null=NULL" -c "SELECT p.code AS project_code, d.code AS device_code FROM projects p LEFT JOIN devices d ON d.project_id = p.id WHERE p.code = 'REVIEW-ROLLBACK-01';"
```

预期返回零行。若显示项目行且设备编码为 NULL，说明项目还在。学习者回复「1」，按达到预期记录，原始查询输出未贴出。

## 4. 修正后用同一编码重试

```cmd
curl.exe -i -X POST "http://127.0.0.1:8000/projects/import" -H "Content-Type: application/json" -d "{\"project_code\":\"REVIEW-ROLLBACK-01\",\"device_codes\":[\"sensor-01\",\"sensor-02\"]}"
```

预期返回 `201 Created`。学习者回复「1」，原始状态行未贴出。

## 5. 查库确认项目和两台设备

```cmd
docker compose exec db psql -U p29 -d p29_lab -c "SELECT p.id AS project_id, p.code AS project_code, d.code AS device_code FROM projects p JOIN devices d ON d.project_id = p.id WHERE p.code = 'REVIEW-ROLLBACK-01' ORDER BY d.code;"
```

预期两行使用同一个项目 ID，设备编码分别为 `sensor-01`、`sensor-02`。学习者回复「1」，原始查询输出未贴出。课后复做时请用新的项目编码，并在两次请求和两次查库中保持一致。

## 自测与讲评

1. 如果应用搬进与 PostgreSQL 相同的 Compose 网络，数据库连接地址怎么写？

   **参考答案**　使用 `db:5432`，库名仍为 `p29_lab`。`db` 是 Compose 服务名。Windows 上运行的应用使用发布地址 `127.0.0.1:55432`。

2. 如果 HTTP 返回 409，但重试前查到项目行和 NULL 设备编码，优先核对哪一处事务边界？

   **参考答案**　检查项目是否在写设备前就单独提交。项目与设备应在同一事务中写入，冲突后按项目编码查库应返回零行。
