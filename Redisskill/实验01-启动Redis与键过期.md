# 实验 01｜启动 Redis 与键过期

## 目标与验收

用 Docker Compose 启动一个本地 Redis 实例，模拟 P29 项目里的设备状态和心跳。完成后你能读写一个 String 键，观察心跳键自动消失，并解释 `TTL` 返回 `-1` 和 `-2` 的区别。

前置条件：Docker Desktop 已启动，使用 Linux 容器。所有 PowerShell 命令都从 `D:\myskills\Redisskill` 执行。通过容器内自带的 `redis-cli` 操作，无需在 Windows 另外安装。

## 第 1 步｜启动并确认连接

在 PowerShell 中执行：

```powershell
Set-Location 'D:\myskills\Redisskill'
docker compose up -d
docker compose ps
docker compose exec -T redis redis-cli PING
```

`up -d` 在后台启动服务，首次可能拉取镜像。最后一条命令应返回 `PONG`。这里的 `redis` 是 [compose.yaml](./compose.yaml) 里的服务名；`-T` 关闭交互终端分配，适合执行单条命令。

端口配置 `127.0.0.1:6380:6379` 表示 Windows 上的客户端连 `127.0.0.1:6380`，容器里的 Redis 监听 `6379`。上面的命令在容器内运行 CLI，因此不传端口时用的是 `6379`。这是本地实验配置，没有设置账号或密码。

**自测：** Windows 上运行的 FastAPI 和 Redis 容器内运行的 CLI，分别使用哪个端口？

## 第 2 步｜写入并读取设备状态

先在 PowerShell 打开交互 CLI：

```powershell
docker compose exec redis redis-cli
```

以下命令在 `redis-cli` 提示符下运行：

```text
SET lab01:project:p29:device:d01:status online
GET lab01:project:p29:device:d01:status
TYPE lab01:project:p29:device:d01:status
TTL lab01:project:p29:device:d01:status
```

预期依次看到 `OK`、`"online"`、`string`、`(integer) -1`。冒号是命名约定，便于看出键属于哪一课、哪个项目和哪台设备。此处没有给状态键设过期时间，所以它存在且没有 TTL；这和数据是否能在重建容器后保留是两回事。

## 第 3 步｜观察心跳过期

在同一个 CLI 中依次输入：

```text
SET lab01:project:p29:device:d01:heartbeat alive EX 30
TTL lab01:project:p29:device:d01:heartbeat
GET lab01:project:p29:device:d01:heartbeat
```

`EX 30` 在写入值的同时设定 30 秒有效期。快速执行时，TTL 应显示 0 到 30 之间的整数，GET 应返回 `"alive"`；如果操作时已经过期，重新运行这组三条命令即可。

等 30 秒，再在 CLI 执行：

```text
GET lab01:project:p29:device:d01:heartbeat
TTL lab01:project:p29:device:d01:heartbeat
```

预期 GET 返回 `(nil)`，TTL 返回 `(integer) -2`，说明键不存在。这里用短期键表达“最近收到过心跳”；设备主数据仍留在数据库。

**自测：** 如果心跳键原来还有 TTL，再对同一个键执行一条不带过期参数的普通 `SET`，新值会自动过期吗？用 `TTL` 验证后再查看 [SET 文档](https://redis.io/docs/latest/commands/set/)。

## 第 4 步｜收尾

还想继续练习，可以留着服务。要清理本课状态键，在 CLI 中执行：

```text
DEL lab01:project:p29:device:d01:status lab01:project:p29:device:d01:heartbeat
QUIT
```

回到 PowerShell 后，如需暂停 Redis，执行 `docker compose stop`；下次用 `docker compose start` 恢复。课程到实验 06 再专门验证持久化和容器重建。

| 现象 | 先检查什么 |
| --- | --- |
| 连接不到 Docker Engine | 打开 Docker Desktop，等引擎就绪，再执行 `docker compose ps` |
| 提示 6380 端口已占用 | 把 Compose 里宿主机端口改成空闲端口，例如 6381，再执行 `docker compose up -d`；容器端口保持 6379 |
| `GET` 提示不是 PowerShell 命令 | 先进入交互式 `redis-cli`；确认终端出现 Redis 提示符再输入 |
| 服务未运行或反复退出 | 在 PowerShell 执行 `docker compose logs --tail 30 redis`，查看第一条启动错误 |

完成后，在 [实验笔记](./实验笔记/README.md) 里新建本课记录，记下你的 `PONG`、心跳过期前后两组输出，以及自测的实测结果。
