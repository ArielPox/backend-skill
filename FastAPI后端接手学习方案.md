# P29 FastAPI 单人后端接手学习方案

> 目标对象：目前只有 1 人负责后端接手、联调、自主开发和独立运维。该人员已掌握前端 Vue3，并了解 FastAPI 基础用法。
>
> 目标结果：不是“看完课程”，而是从“会写 FastAPI 基础接口”升级为“能接手生产级 FastAPI 后端”，可独立完成源码接收、接口维护、数据库迁移、设备数据链路理解、任务调度、部署运维、日志排障和小版本发布。

## 动手实验教学约定

1. **先讲目标和验收标准。** 开始一课时，说明要做出什么、最后看到什么算成功。先讲当前实验需要的知识，再开始操作。
2. **一次只做一个可验证的步骤。** 我说“继续”时，只给下一步。说明在哪个目录、哪个终端执行，给出可复制的命令，解释关键参数，并告诉我应该看到什么。
3. **根据实际输出排错。** 我贴出报错或截图时，先指出关键报错，解释失败发生在哪个环节，再给一个检查或修复动作。修复后从卡住的地方接着做。
4. **用自测检查理解。** 每个关键小节给一道与刚才操作相关的题。我回答后，指出答对的部分，再纠正容易混淆的地方。比如区分宿主机端口、容器监听端口和服务间访问地址。
5. **复杂案例先梳理全局。** 涉及多个服务时，先画一条简单的请求链路，再分别说明服务怎么启动、配置写在哪个文件、数据存在哪里。如果我说“有点乱”，先讲清目前做到哪一步，再继续操作。
6. **用实际操作验收，结课前保存笔记。** 比如用 HTTP 响应验证网页可用，用重建容器后查到旧数据验证持久化。每课结束前，把知识点、命令、预期结果、实际遇到的报错和自测整理成 Markdown，保存到当前工作区的实验笔记目录。本课程的目录是 `D:\myskills\FastAPI实验笔记`。课程完成后，将实际执行的操作按顺序保存到该课程的 Markdown 实验笔记中。每步记录执行目录、终端、可复制的命令或文件改动、预期和实际结果。遇到报错时，保留关键报错、有效的修复步骤和复验结果，方便课后从头复做。

## 0. 已有基础与学习策略调整

由于负责人已经掌握 Vue3，并知道 FastAPI 基础用法，学习计划不再从前端和 FastAPI 入门开始，而是转向生产接手能力。

| 已具备能力 | 可以减少的学习内容 | 需要强化的方向 |
| --- | --- | --- |
| Vue3 前端基础 | 不再安排 Vue3 系统学习 | 利用前端代码反推接口、字段、页面数据链路 |
| FastAPI 基础用法 | 不再重复路由、请求体、基础 Pydantic 教程 | 强化项目结构、依赖注入、鉴权、异常处理、中间件、部署 |
| 前后端联调经验 | 不再单独学习 HTTP 基础 | 直接围绕 `/api/v1`、token、WebSocket、文件流做实战 |

新的学习策略：

1. **少看入门课，多做接手演练**。
2. **每个知识点都要绑定 P29 场景**，例如项目树、设备详情、告警、QA、报表、邮件、标定。
3. **优先补后端生产短板**：数据库、迁移、Redis、任务、MQTT、WebSocket、部署、日志、排障。
4. **以能交接为目标**：学习过程中同步形成问题清单，后续向厂商提问。

## 1. 学习总目标

这个人最终必须具备以下 8 项能力：

| 能力 | 最低达标标准 |
| --- | --- |
| FastAPI 接口开发 | 能读懂项目路由、依赖注入、Pydantic 模型、异常处理，能新增/修改 `/api/v1` 接口 |
| 数据库开发 | 能维护 SQLAlchemy 模型、查询、事务、索引，能使用 Alembic 做迁移 |
| 鉴权权限 | 能理解 Bearer Token、JWT、Refresh Token、用户角色、接口权限 |
| Redis/缓存 | 能理解缓存、TTL、任务状态、token 黑名单、分布式锁基础用法 |
| 后台任务 | 能维护 APScheduler/Celery 定时任务、任务日志、失败重试和补偿任务 |
| WebSocket | 能维护 FastAPI WebSocket 鉴权、消息推送、断线重连和消息类型 |
| 设备/MQTT | 能理解 MQTT topic、设备上报、在线状态、告警、标定命令链路 |
| 部署运维 | 能用 nginx + Uvicorn/Gunicorn/systemd 或 Docker 部署、查看日志、备份恢复、发布回滚 |

## 2. 权威官方文档清单

优先级分为：

- **P0 必学**：没有这个无法接手。
- **P1 必会**：接手后一个月内必须能用。
- **P2 加强**：用于优化、扩展和长期维护。

| 技术栈 | 优先级 | 官方文档 | 学习重点 |
| --- | --- | --- | --- |
| Python 环境 | P0 | [Python Packaging: venv 与 pip](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) | 虚拟环境、依赖安装、requirements、环境隔离 |
| Python 日志 | P0 | [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html) | logger、日志级别、文件日志、排障日志 |
| Python asyncio | P1 | [Python asyncio 开发指南](https://docs.python.org/3/library/asyncio-dev.html) | async/await、协程、事件循环、异步排障 |
| FastAPI | P0 | [FastAPI 官方教程](https://fastapi.tiangolo.com/tutorial/) | 路由、请求体、响应模型、依赖注入、OpenAPI |
| FastAPI 学习入口 | P0 | [FastAPI Learn](https://fastapi.tiangolo.com/learn/) | 官方推荐学习路径 |
| FastAPI 安全 | P0 | [OAuth2 + JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) | 登录、token、JWT、密码哈希 |
| FastAPI WebSocket | P1 | [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) | 连接、消息、断开、异常处理 |
| FastAPI 测试 | P1 | [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/) | TestClient、pytest、接口回归 |
| FastAPI 异步测试 | P1 | [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/) | httpx、异步接口测试 |
| FastAPI 部署 | P0 | [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/) | 生产部署概念、进程、代理、HTTPS |
| FastAPI Docker | P1 | [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/) | Dockerfile、镜像、容器部署 |
| Pydantic | P0 | [Pydantic Docs](https://docs.pydantic.dev/latest/) | 请求/响应 DTO、字段校验、序列化 |
| Uvicorn | P0 | [Uvicorn Deployment](https://www.uvicorn.org/deployment/) | 本地启动、workers、nginx 后部署 |
| SQLAlchemy | P0 | [SQLAlchemy Unified Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/) | Engine、Session、ORM、查询、事务 |
| Alembic | P0 | [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) | migration、版本、升级、回滚 |
| Redis Python | P1 | [redis-py 官方指南](https://redis.io/docs/latest/develop/clients/redis-py/) | 连接、String/Hash/Set、TTL、pipeline |
| Redis University | P1 | [Redis University](https://redis.io/tutorials/university/) | Redis 系统课程、练习和认证 |
| APScheduler | P1 | [APScheduler User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) | 定时任务、trigger、job store、executor |
| Celery | P1 | [Celery Introduction](https://docs.celeryq.dev/en/main/getting-started/introduction.html) | 异步任务、worker、broker、重试 |
| MQTT 协议 | P1 | [Eclipse Mosquitto MQTT 文档](https://mosquitto.org/man/mqtt-7.html) | pub/sub、topic、QoS、broker |
| Mosquitto Broker | P1 | [Mosquitto Documentation](https://www.mosquitto.org/documentation/) | broker、mosquitto_pub/sub、配置 |
| Paho MQTT Python | P1 | [Eclipse Paho Python Client](https://eclipse.dev/paho/clients/python/docs/) | Python 订阅/发布、回调、重连 |
| Docker | P1 | [Docker Get Started](https://docs.docker.com/get-started/) | 镜像、容器、compose、部署一致性 |
| nginx | P0 | [nginx Beginner’s Guide](https://nginx.org/en/docs/beginners_guide.html) | 启停、配置结构、静态文件、proxy |
| nginx 反代 | P0 | [NGINX Reverse Proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/) | API 反向代理、WebSocket 代理 |
| pytest | P1 | [pytest Get Started](https://pytest.org/en/latest/getting-started.html) | 单元测试、接口测试、fixture |
| OpenAI API | P2 | [OpenAI Developer Quickstart](https://developers.openai.com/api/docs/quickstart) | Python SDK、API key、模型调用 |
| OpenAI Python SDK | P2 | [openai-python](https://github.com/openai/openai-python) | 同步/异步 client、Responses API |

## 3. 视频课程清单

视频课只作为“加速理解”，真正掌握必须落到练习和项目产出。

| 主题 | 推荐视频/课程 | 权威性 | 使用方式 |
| --- | --- | --- | --- |
| FastAPI 入门与 API 集成 | [freeCodeCamp: Modern Python with FastAPI](https://www.youtube.com/watch?v=rkPIftzu1pQ) | freeCodeCamp 大型公益课程，项目式讲解 | 第 1-2 周配合官方文档看，重点学 FastAPI + PostgreSQL + API 集成 |
| SQLAlchemy 2.0 | [Mike Bayer: SQLAlchemy 2.0 Tutorial](https://www.youtube.com/watch?v=Uym2DHnUEno) | SQLAlchemy 作者 Mike Bayer 授课 | 第 3 周看，必须边看边写 ORM、Session、查询 |
| Redis | [Redis University](https://redis.io/tutorials/university/) | Redis 官方课程平台 | 第 5 周学习 Redis 基础和 Python 使用 |
| Redis Python 开发 | [Redis for Python Developers](https://redis.io/blog/redis-for-python-developers-course-redis-university/) | Redis 官方课程介绍 | 作为 Redis 深入学习路线 |
| Docker | [Docker Learning Paths](https://www.docker.com/learning-paths/learning-basics/) | Docker 官方学习路径 | 第 8 周学习容器和 compose |
| OpenAI API | [OpenAI Developer Quickstart](https://developers.openai.com/api/docs/quickstart) | OpenAI 官方 quickstart，含 Python SDK | 第 10 周用于 AI 问答链路理解 |

说明：

- FastAPI 最权威的学习材料其实是官方文档，不是视频。
- SQLAlchemy 建议优先看作者 Mike Bayer 的视频，比多数二手教程可靠。
- Redis 优先用 Redis University，因为有结构化课程和练习。
- nginx、Linux、systemd、MQTT 更建议看官方文档并做实验，视频质量参差不齐。

## 4. 12 周学习与接手计划

如果这个人还要兼顾日常工作，建议按 **8 周进阶接手版** 执行。每天至少 2 小时，周末半天做实战。如果能全职学习，可压缩到 5-6 周。

原 12 周路线仍可作为保底路线；但基于当前基础，推荐直接执行下面的 8 周计划。

## 4A. 8 周进阶接手计划

### 第 1 周：前端反推接口 + FastAPI 项目结构进阶

目标：把前端已有 Vue3 经验转化为后端接手优势，能从前端页面定位后端接口、字段和业务链路。

学习内容：

- 前端 `src/api`、`src/store`、`src/views` 如何反推后端接口。
- FastAPI 生产项目常见目录结构。
- APIRouter 分模块。
- Depends 依赖注入。
- Middleware。
- 统一响应和异常处理。
- OpenAPI 文档整理。

练习产出：

- 梳理 P29 前端核心页面到接口的映射表：
  - 登录。
  - 项目树。
  - 设备详情。
  - 告警列表。
  - AI 问答。
  - 邮件通知。
- 搭建一个 P29 风格 FastAPI mock 后端，统一 `/api/v1` 前缀。
- 实现统一响应：

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

验收标准：

- 能说明某个 Vue 页面调用了哪个后端接口。
- 能解释 FastAPI 的 router、schema、service、repository 分层。
- 能用 mock 后端替代部分真实接口供前端联调。

### 第 2 周：鉴权权限 + 前后端登录闭环

目标：能接手登录、token、用户信息、权限控制。

学习内容：

- JWT。
- OAuth2PasswordBearer。
- Refresh Token。
- RBAC。
- token 过期和刷新。
- 前端 axios 拦截器与后端鉴权的配合。

练习产出：

- 实现：
  - `POST /api/v1/system/auth/login`
  - `GET /api/v1/system/auth/userinfo`
  - `POST /api/v1/system/auth/refresh`
  - `POST /api/v1/system/auth/logout`
- 前端可真实登录 mock 后端。
- 设计用户、角色、权限三张表。

验收标准：

- 能解释前端 `Authorization: Bearer token` 到后端用户身份的全过程。
- 能处理 401、token 过期、刷新 token、退出登录。
- 能判断某接口是否需要权限控制。

### 第 3 周：SQLAlchemy + Alembic + 数据建模

目标：能维护 P29 项目、设备、告警、用户、配置类数据表。

学习内容：

- SQLAlchemy 2.0 ORM。
- Session 生命周期。
- 事务。
- 分页查询。
- 索引。
- Alembic migration。
- 数据库初始化数据。

练习产出：

- 建表：
  - `users`
  - `roles`
  - `projects`
  - `devices`
  - `alarms`
  - `qa_sessions`
  - `mail_accounts`
- 实现：
  - 项目树查询。
  - 设备分页搜索。
  - 告警按时间和状态查询。
- 编写 Alembic migration。

验收标准：

- 能从空库初始化。
- 能升级/回滚 migration。
- 能给慢查询加索引。
- 能解释前端字段对应哪个表、哪个字段、哪个计算口径。

### 第 4 周：Redis + 后台任务 + 健康检查

目标：能维护在线状态、缓存、任务状态、健康检查和补偿任务。

学习内容：

- redis-py。
- TTL。
- 缓存失效。
- 任务状态缓存。
- APScheduler 或 Celery。
- 任务失败重试。
- job 日志。
- 健康检查接口。

练习产出：

- 设备心跳写 Redis。
- 项目树缓存 60 秒。
- 定时任务生成在线状态汇总。
- 提供：
  - `GET /api/v1/diagnosis/qa-health/summary`
  - `GET /api/v1/system/jobs/latest`
  - `POST /api/v1/system/jobs/{job_name}/run`

验收标准：

- 能解释前端健康页的后端数据来源。
- 能定位某个任务为什么没有执行。
- 能手动触发一次补偿任务。

### 第 5 周：MQTT 设备接入 + 告警链路

目标：能理解设备数据从上报到页面展示的完整链路。

学习内容：

- MQTT topic。
- QoS。
- Paho MQTT。
- Mosquitto。
- 设备编号映射。
- 最新值入 Redis。
- 历史值入库。
- 告警规则生成。

练习产出：

- 本地 Mosquitto broker。
- 模拟设备上报：
  - SOC。
  - SOH。
  - 电压。
  - 温度。
  - 状态。
- 后端消费后写入 Redis/DB。
- 电压低于阈值生成告警。
- 前端设备详情接口能查到最新值和告警。

验收标准：

- 能画出设备数据链路。
- 能解释 `device_no`、`device_id`、`protocol_device_no` 的区别。
- 能定位“页面数据不刷新”可能是哪一环出问题。

### 第 6 周：WebSocket + 标定下发安全链路

目标：能维护实时推送和设备命令类高风险能力。

学习内容：

- FastAPI WebSocket。
- token query 鉴权。
- Connection Manager。
- 心跳与断线重连。
- 标定点位白名单。
- 写入值域校验。
- 命令幂等。
- 命令状态机。
- 操作审计。

练习产出：

- 实现：
  - `/api/v1/diagnosis/ws?token=...`
- 推送：
  - `device_status`
  - `alarm_created`
  - `job_status`
- 模拟标定命令：
  - 创建命令。
  - 校验点位。
  - 发布 MQTT command。
  - 模拟设备回执。
  - 更新命令状态。

验收标准：

- 能解释前端 WebSocket 断线重连逻辑。
- 能解释标定下发为什么必须有白名单、值域、幂等、审计。
- 能查到每条命令是谁发的、发给谁、结果是什么。

### 第 7 周：部署、日志、监控、发布回滚

目标：能独立部署和排障。

学习内容：

- Uvicorn/Gunicorn。
- nginx reverse proxy。
- WebSocket proxy。
- systemd。
- Docker compose。
- 日志分级。
- 环境变量。
- 备份恢复。
- 发布和回滚。

练习产出：

- 写出：
  - `nginx.conf`
  - `p29-api.service`
  - `Dockerfile`
  - `docker-compose.yml`
  - `.env.example`
- 部署 FastAPI、Redis、MQTT、数据库。
- 完成一次发布和回滚演练。
- 完成一次数据库备份恢复。

验收标准：

- 能从零部署。
- 能重启服务。
- 能查看 nginx、API、worker 日志。
- 能定位 500 错误。
- 能回滚上一版本。

### 第 8 周：AI 问答 + Golden 回归 + 综合接手演练

目标：能看懂并维护 P29 AI 问答能力，不把 AI 当黑盒。

学习内容：

- Prompt 模板。
- 上下文构造。
- 意图路由。
- LLM fallback。
- QA 反馈。
- Golden Case。
- 回归测试。
- 模板发布/回滚。

练习产出：

- 实现简化版：
  - `POST /api/v1/diagnosis/qa/session`
  - `POST /api/v1/diagnosis/qa/ask`
  - `POST /api/v1/diagnosis/qa/feedback`
- 构造 5 条 Golden Case。
- 修改模板并跑回归。
- 做一次综合演练：
  - 前端登录。
  - 项目树展示。
  - 模拟设备上报。
  - 告警生成。
  - WebSocket 推送。
  - QA 查询设备状态。
  - 发布一次小改动。
  - 回滚。

验收标准：

- 能解释 QA 链路：问题 -> 意图 -> 上下文 -> 模板 -> 模型 -> 答案 -> 反馈。
- 能判断回答错误是数据问题、模板问题、规则问题还是模型问题。
- 能完成一次完整 P29 接手演练。

## 4B. 12 周保底计划

如果执行 8 周计划过程中发现 Python、数据库或部署基础不足，再按下面 12 周计划补齐。

### 第 1 周：Python 工程基础 + FastAPI 入门

目标：能启动一个 FastAPI 服务，理解 `/docs`、路由、请求体、响应模型。

学习内容：

- Python venv、pip、requirements。
- FastAPI 基础路由。
- Pydantic 请求/响应模型。
- OpenAPI 自动文档。

练习产出：

- 新建一个 `p29-training-api` 小项目。
- 实现：
  - `GET /health`
  - `GET /api/v1/projects`
  - `POST /api/v1/devices`
- 所有接口统一返回：

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

验收标准：

- 能用 `uvicorn main:app --reload` 启动。
- 能打开 `/docs` 调试接口。
- 能解释 FastAPI 路由、Pydantic 模型和 OpenAPI 的关系。

### 第 2 周：FastAPI 项目结构 + 鉴权 JWT

目标：能看懂并维护 P29 登录、token、用户信息、权限类接口。

学习内容：

- APIRouter 分模块。
- Depends 依赖注入。
- OAuth2PasswordBearer。
- JWT 生成、解析、过期。
- 密码哈希。
- 统一异常处理。

练习产出：

- 实现：
  - `POST /api/v1/system/auth/login`
  - `GET /api/v1/system/auth/userinfo`
  - `POST /api/v1/system/auth/refresh`
  - `POST /api/v1/system/auth/logout`
- 登录后返回 `access_token` 和 `refresh_token`。
- 受保护接口必须带 `Authorization: Bearer token`。

验收标准：

- 能解释前端 `Authorization: Bearer <token>` 如何被后端校验。
- 能模拟 token 过期和刷新。
- 能说明 401 与业务错误码的区别。

### 第 3 周：SQLAlchemy + Alembic

目标：能维护项目、设备、用户、告警、配置类数据库表。

学习内容：

- SQLAlchemy Engine、Session、ORM Model。
- 一对多、多对一关系。
- 查询、分页、事务。
- Alembic 初始化、自动生成 migration、升级和回滚。
- 索引和唯一约束。

练习产出：

- 建表：
  - `users`
  - `projects`
  - `devices`
  - `alarms`
- 实现：
  - 项目列表分页。
  - 设备列表搜索。
  - 告警按设备和时间范围查询。
- 写 2 个 Alembic migration：
  - 初始建表。
  - 给 `devices.device_no` 增加唯一索引。

验收标准：

- 能从空库初始化表结构。
- 能升级/回滚 migration。
- 能解释 Session 生命周期和事务提交。

### 第 4 周：对接前端接口规范

目标：能按照现有前端约定实现接口。

学习内容：

- 前端 `/api/v1` 约定。
- `{ code, msg, data }` 响应封装。
- 分页返回。
- 文件下载。
- 错误码。
- `X-Locale` 语言头。

练习产出：

- 实现模拟接口：
  - `/api/v1/projects/tree?source=semantic`
  - `/api/v1/projects/box/{deviceId}/brief`
  - `/api/v1/device/registry/list`
  - `/api/v1/device/detail/chr/device/{deviceId}/alarms`
  - `/api/v1/device/detail/chr/device/{deviceId}/alarms/export`

验收标准：

- 用前端或接口工具能正常调通。
- blob 导出能下载 CSV。
- 错误时前端可读 `msg`。

### 第 5 周：Redis + 缓存 + 在线状态

目标：能理解在线状态、缓存、任务状态和 token 黑名单。

学习内容：

- redis-py。
- String、Hash、Set。
- TTL。
- pipeline。
- 简单分布式锁。
- 缓存穿透和缓存失效。

练习产出：

- 设备最新心跳写入 Redis。
- 根据最后心跳时间计算在线/离线。
- 登录退出时把 token jti 放入 Redis 黑名单。
- 项目树缓存 60 秒。

验收标准：

- 能用 Redis CLI 查看 key。
- 能解释 TTL 到期后页面数据如何刷新。
- 能说明哪些数据适合 Redis，哪些必须落数据库。

### 第 6 周：后台任务 APScheduler/Celery

目标：能维护汇总任务、邮件任务、健康检查、Golden 回归任务。

学习内容：

- APScheduler trigger、job store、executor。
- Celery broker、worker、task、retry。
- 任务日志。
- 任务幂等。
- 任务失败补偿。

练习产出：

- 用 APScheduler 每分钟生成一次设备在线状态汇总。
- 用 Celery 或模拟 worker 发送一条邮件任务。
- 记录任务执行状态：
  - queued
  - running
  - success
  - failed
- 提供接口：
  - `GET /api/v1/system/jobs/latest`
  - `POST /api/v1/system/jobs/{job_name}/run`

验收标准：

- 能手动触发任务。
- 能查看任务日志。
- 能解释任务失败如何重试和补偿。

### 第 7 周：MQTT + 设备数据链路

目标：能理解设备数据从 MQTT 到数据库/Redis/前端的链路。

学习内容：

- MQTT pub/sub。
- topic 设计。
- QoS。
- Paho Python 客户端。
- Mosquitto 本地 broker。
- 设备数据解析。

练习产出：

- 本地启动 Mosquitto。
- 用 `mosquitto_pub` 发布模拟设备数据。
- Python 订阅 topic，把数据写入 Redis 和数据库。
- 实现：
  - 设备最新 SOC/SOH。
  - 在线状态。
  - 简单告警：电压低于阈值生成告警。

验收标准：

- 能画出：设备 -> MQTT -> 后端 consumer -> Redis/DB -> 前端接口。
- 能解释 topic、device_no、device_id 的关系。
- 能模拟一条设备上报并在接口中查到。

### 第 8 周：WebSocket + 实时推送

目标：能维护 `/api/v1/diagnosis/ws`。

学习内容：

- FastAPI WebSocket。
- token query 鉴权。
- 连接管理。
- 心跳。
- 断线重连。
- 消息类型设计。

练习产出：

- 实现：
  - `/api/v1/diagnosis/ws?token=...`
- 推送消息类型：
  - `device_status`
  - `alarm_created`
  - `job_status`
- MQTT 收到设备数据后，向 WebSocket 客户端推送最新状态。

验收标准：

- 前端或 WebSocket 工具可连接。
- token 错误时拒绝连接。
- 断线后重连不导致服务崩溃。

### 第 9 周：部署 nginx + Uvicorn/Gunicorn + Docker

目标：能独立部署测试环境。

学习内容：

- Uvicorn 启动参数。
- Gunicorn/Uvicorn worker。
- nginx reverse proxy。
- WebSocket proxy。
- systemd service。
- Dockerfile 和 docker compose。

练习产出：

- 写出：
  - `Dockerfile`
  - `docker-compose.yml`
  - `nginx.conf`
  - `p29-api.service`
- 部署一个可访问的测试服务。
- nginx 将 `/api/v1` 转发到 FastAPI。
- nginx 支持 WebSocket。

验收标准：

- 能重启 API 服务。
- 能 reload nginx。
- 能查看 systemd 日志。
- 能说明生产环境为什么不能只用 `uvicorn --reload`。

### 第 10 周：日志、监控、测试与排障

目标：能独立定位接口错误、任务失败、数据库慢查询。

学习内容：

- Python logging。
- 请求日志。
- 错误堆栈。
- pytest。
- FastAPI TestClient。
- httpx 异步测试。
- 慢查询和索引。

练习产出：

- 给所有接口加请求日志。
- 写测试：
  - 登录成功/失败。
  - 项目树接口。
  - 设备告警分页。
  - WebSocket 鉴权失败。
- 模拟一个任务失败并记录错误。

验收标准：

- 能通过日志定位接口 500。
- 能运行 `pytest`。
- 能解释测试失败原因。

### 第 11 周：AI 问答、模板、Golden 回归

目标：能理解 P29 的 AI 问答后端不是黑盒。

学习内容：

- OpenAI Python SDK 或实际厂商模型 SDK。
- Prompt 模板。
- 上下文构造。
- 规则命中与 LLM fallback。
- Golden Case。
- 回归测试。

练习产出：

- 实现一个简化版：
  - `POST /api/v1/diagnosis/qa/session`
  - `POST /api/v1/diagnosis/qa/ask`
  - `POST /api/v1/diagnosis/qa/feedback`
- 使用设备上下文回答：
  - “这个设备当前 SOC 是多少？”
  - “最近有哪些告警？”
- 建 5 条 Golden Case，写一个回归脚本。

验收标准：

- 能解释：问题 -> 意图 -> 上下文 -> 模板 -> 模型 -> 答案 -> 反馈。
- 能修改模板并跑回归。
- 能定位回答错误是数据问题、模板问题还是模型问题。

### 第 12 周：P29 接手综合演练

目标：完成一次完整接手闭环。

综合任务：

1. 从空环境部署 FastAPI 服务。
2. 初始化数据库。
3. 启动 Redis。
4. 启动 MQTT broker。
5. 启动后台任务。
6. nginx 反代 `/api/v1` 和 WebSocket。
7. 前端连接测试环境。
8. 模拟设备数据上报。
9. 页面看到项目树、设备状态、告警。
10. 修改一个接口字段并发布。
11. 执行一次回滚。
12. 备份并恢复数据库。

最终验收标准：

- 能独立部署。
- 能独立联调前端。
- 能独立排查一个 500 错误。
- 能独立新增一个接口字段。
- 能独立处理一次任务失败。
- 能独立解释设备数据链路。
- 能独立完成发布和回滚。

## 5. 每周学习节奏

建议这个人按下面节奏执行：

| 时间 | 内容 |
| --- | --- |
| 周一 | 看官方文档，整理笔记 |
| 周二 | 跟着文档写最小 demo |
| 周三 | 看视频课对应章节，补理解 |
| 周四 | 把 demo 改造成 P29 风格 |
| 周五 | 写测试、补日志、整理问题 |
| 周六 | 做本周综合练习 |
| 周日 | 复盘：输出一页学习记录和一张流程图/链路图 |

## 6. 学习过程必须输出的文件

每周必须有产物，不能只看课。

| 周次 | 必交产物 |
| --- | --- |
| 第 1 周 | FastAPI demo、接口截图、学习笔记 |
| 第 2 周 | JWT 登录 demo、token 流程图 |
| 第 3 周 | SQLAlchemy 模型、Alembic migration |
| 第 4 周 | P29 风格接口 mock 服务 |
| 第 5 周 | Redis 在线状态 demo |
| 第 6 周 | 定时任务和任务日志 demo |
| 第 7 周 | MQTT 设备上报 demo |
| 第 8 周 | WebSocket 推送 demo |
| 第 9 周 | nginx + API 部署记录 |
| 第 10 周 | pytest 测试报告和排障记录 |
| 第 11 周 | QA 简化链路和 Golden Case |
| 第 12 周 | 综合演练报告 |

## 7. 这个人需要达到的能力分级

### A 级：可以参与接手

- 能看懂 FastAPI 路由和 Pydantic 模型。
- 能启动后端。
- 能改简单接口字段。
- 能执行数据库 migration。

### B 级：可以独立维护

- 能新增接口。
- 能处理登录鉴权问题。
- 能排查数据库和 Redis 问题。
- 能维护定时任务。
- 能看懂 MQTT 数据链路。

### C 级：可以独立负责 P29 后端

- 能独立部署、发布、回滚。
- 能处理生产接口故障。
- 能维护 WebSocket、任务调度、报表、邮件。
- 能修改 AI 模板并做 Golden 回归。
- 能处理设备数据异常和告警规则问题。

本方案的目标是让负责人至少达到 **B 级**，试运行期冲刺到 **C 级**。

## 8. 优先级建议

如果时间紧，只学最关键内容，顺序如下：

1. FastAPI + Pydantic。
2. JWT 鉴权。
3. SQLAlchemy + Alembic。
4. 前端 `/api/v1` 接口联调。
5. nginx + Uvicorn 部署。
6. Redis。
7. 后台任务。
8. MQTT。
9. WebSocket。
10. AI 问答与 Golden 回归。

## 9. 管理建议

因为目前只有 1 人负责，建议管理上做三件事：

1. **保证学习时间**：前 4 周每天至少 2 小时连续学习和练习。
2. **要求每周产物**：没有 demo 和测试，不算学完。
3. **让厂商配合答疑**：学习到第 4 周后，拿前端接口清单和 demo 去问厂商真实代码结构、数据库结构和部署方式。

最终判断标准很简单：这个人能不能从零部署一个简化版 P29 后端，并让前端跑通核心链路。能做到，后续接手才有底。
