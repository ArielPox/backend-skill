# Redis 后端实战课件

对应 [课程计划](../course-plan.md)。在 VS Code 打开 `D:\myskills\Redisskill`，使用集成 PowerShell。课堂互动时每次“继续”只执行一个可验证步骤。完成每课后另存实验笔记，记录实际命令、结果、故障和自测。

## 全局数据链路

设备详情请求 → FastAPI 校验项目权限 → Redis 读缓存 → 未命中时查 PostgreSQL → 带 TTL 回填 Redis → 响应。PostgreSQL 保存设备主数据。Redis 保存可重建的缓存、心跳和计数。缓存键同时包含项目 ID 与设备 ID。

## 第 1 课｜启动 Redis 与键过期

**目标与验收**　得到 `PONG`，写入状态和心跳键，实际观察 TTL 的非负值、`-1`、`-2`。

**先知道**　`127.0.0.1:6380:6379` 表示宿主机端口 6380 映射到容器端口 6379。容器内 `redis-cli` 使用 6379。TTL 非负表示剩余秒数，`-1` 表示存在但无过期时间，`-2` 表示键不存在。

1. 在集成 PowerShell 执行 `Set-Location 'D:\myskills\Redisskill'`、`docker compose up -d`、`docker compose exec -T redis redis-cli PING`。预期 `PONG`。
2. 进入 `docker compose exec redis redis-cli`，执行 `SET lab01:project:p29:device:d01:status online`、`GET ...:status` 与 `TTL ...:status`。预期值为 `online`，TTL 为 `-1`。
3. 执行 `SET lab01:project:p29:device:d01:heartbeat alive EX 30`，立即查询 TTL，等待 30 秒后再次执行 `GET` 和 `TTL`。预期过期后分别为 nil 和 `-2`。

**自测**　一个带 TTL 的键被普通 `SET` 覆盖后，新值是否继续自动过期？用 `TTL` 实测。

完整可复制命令、收尾和排错表见 [第 1 课原实验材料](../lab-01-start-redis-and-key-expiration.md)。

## 第 2 课｜给业务数据选结构

**目标与验收**　能修改单个设备状态字段、判断设备是否在线、列出分值最高的三条告警，并用 SCAN 分批浏览实验键。

**先知道**　Hash 适合单设备多个字段，Set 适合集合成员判断，ZSet 适合带分值排序。键命名应包含项目范围，避免不同项目的相同设备编码串数据。

1. 在 VS Code 集成 PowerShell 打开 `redis-cli`，逐条执行并观察返回值。

   ```text
   HSET lab02:p29:device:d01 status online battery 88
   HGETALL lab02:p29:device:d01
   HSET lab02:p29:device:d01 battery 87
   HGET lab02:p29:device:d01 battery
   SADD lab02:p29:online d01 d02
   SISMEMBER lab02:p29:online d01
   ZADD lab02:p29:alarms 100 alarm-a 80 alarm-b 120 alarm-c
   ZREVRANGE lab02:p29:alarms 0 2 WITHSCORES
   SCAN 0 MATCH lab02:* COUNT 10
   ```

2. 预期电量更新为 87，集合成员查询返回 1，告警按 120、100、80 降序。`SCAN` 返回的游标若非 0，继续用新游标查询，直到返回 0。

**自测**　为什么在线设备成员判断用 Set 比把所有设备编码塞进一个普通字符串更直接？

## 第 3 课｜FastAPI 接入读缓存

**目标与验收**　同一设备详情第一次请求查库并回填，第二次命中缓存，过期后再次查库。用日志或查库次数证明三种路径。

**先知道**　Cache-aside 由应用负责读缓存、回源和回填。先验证调用者对项目的权限，再查缓存。连接在应用 lifespan 中建立和关闭，Redis 操作设置有限超时。

1. 在 VS Code 中核对 [数据库课程](../../SQLAIchemy-AIembic-skill/course-plan.md)的设备模型和 FastAPI 设备详情接口。确定缓存键格式 `device:{project_id}:{device_id}`，记录 Redis 服务地址和 TTL。
2. 在接口中先按项目权限校验，再从 Redis 读取；命中时反序列化并返回。未命中时按同一项目和设备 ID 查询 PostgreSQL，查不到返回 404，查到则带 TTL 写入 Redis 并返回。
3. 在集成 PowerShell 连续调用同一详情接口两次，核对日志中的数据库查询次数；用 `redis-cli TTL` 看剩余时间。等键过期后再次调用并核对回源。

**自测**　Redis 命中了设备 ID，却属于另一项目时，为什么仍不能直接返回？

## 第 4 课｜更新、失效与故障降级

**目标与验收**　设备更新后下一次读到新值。停止 Redis 后接口仍能从 PostgreSQL 查设备。

**先知道**　更新先提交 PostgreSQL 事务，再删除对应 Redis 键。先删缓存再提交时，另一个请求可能读取旧数据库值并回填。并发下即使按提交后删除，仍要考虑旧读请求延迟回填的竞态。

1. 先连续读取同一设备，确认缓存命中。通过更新接口修改设备状态，查询数据库确认新值，再执行缓存失效。
2. 下一次读取应先 Redis 未命中，再查数据库并回填新值。再读一次应命中新缓存。保留接口响应和查库日志。
3. 在隔离实验中执行 `docker compose stop redis`，重试详情接口。预期记录 Redis 错误并降级查库。完成后执行 `docker compose start redis`，复验正常链路。

**自测**　如果先删除缓存，数据库事务还没提交，另一请求可能缓存什么值？

## 第 5 课｜计数、限流与原子性

**目标与验收**　同一项目固定窗口内超过阈值返回 429，窗口过期后可再次请求。并发请求不会让首次计数键永久无 TTL。

**先知道**　`INCR` 与首次 `EXPIRE` 分为两条命令时，中途失败可能留下无过期时间的键。用 Lua 脚本把计数和首次设过期合为一个原子操作。固定窗口的边界突发由业务限流要求决定。

1. 在独立实验键上演示 `INCR lab05:p29:count`、`TTL lab05:p29:count`，观察第一次计数后尚无 TTL 的状态，再清理该实验键。
2. 将 `INCR` 和首次 `EXPIRE` 放入 Lua 脚本，由接口按项目 ID 执行。连续发送高于阈值的请求，记录允许次数、429 次数和计数键 TTL。
3. 等窗口过期后再次请求，确认重新开始计数。在并发请求中核对实际允许数量和 TTL。

**自测**　为什么限流键必须包含项目 ID？

## 第 6 课｜持久化、内存与排障

**目标与验收**　用同一命名卷重建 Redis 容器，检查指定键是否保留。区分键主动过期与内存淘汰。

**先知道**　RDB 与 AOF 是持久化机制，TTL 到期和内存淘汰是不同的键消失原因。重建容器时要确认 Compose 挂载的仍是同一命名卷。

1. 在独立实验实例核对 Compose 中的卷挂载和 Redis 持久化配置，写入一个无 TTL 实验键与一个短 TTL 键。
2. 记录 `INFO persistence`、`INFO stats` 和 `TTL`，按课程计划用原命名卷重建容器，再查两个键。把结果与当前持久化模式对应起来。
3. 在独立、可清理的实例中设置受控内存上限与淘汰策略，制造淘汰。对比 `expired_keys` 与 `evicted_keys` 的变化，保留 `INFO` 输出。

**自测**　键在重建后不存在，为什么只看一次 `GET` 不能判断它是过期、淘汰还是未持久化？

## 第 7 课｜项目综合验收

**目标与验收**　两个项目的设备缓存不串，命中、更新、过期、Redis 故障均有测试和实际结果。

1. 准备两个项目及各自设备，确认缓存键包含项目与设备标识。分别请求并检查响应和 Redis 键。
2. 执行缓存命中、更新失效、TTL 到期和停 Redis 四组实验，记录 HTTP 状态、业务字段、查库次数及日志。
3. 用独立测试库运行集成测试。检查访问控制先于缓存读取，项目不存在和设备不存在时不会泄露其他项目的数据。

**自测**　两个项目使用相同设备编码，缓存键仅包含设备编码会造成什么错误？

## 选修｜告警消息与 Streams

**目标与验收**　模拟消费者在确认前退出，恢复后处理待确认消息；按告警 ID 去重。

**先知道**　Pub/Sub 的在线订阅与 Streams 消费组的待确认消息适用于不同交付要求。消费消息的业务处理和 `XACK` 之间可能失败，处理逻辑应具备幂等性。

1. 在隔离实验键上创建 Stream 与消费组，写入一条合成告警，使用 `XREADGROUP` 领取。
2. 不执行 `XACK` 就退出消费者，检查待处理项，再启动恢复消费者重新认领并处理。
3. 以告警 ID 做业务去重，处理成功后 `XACK`，核对待处理数量和业务结果。

**自测**　为什么仅使用 `XACK` 不能保证数据库业务操作恰好执行一次？
