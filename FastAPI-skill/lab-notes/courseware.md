# FastAPI 后端接手实战课件

对应 [课程计划](../course-plan.md)。在 VS Code 打开 `D:\myskills\FastAPI-skill`，使用集成 PowerShell 终端。先按每课的目标和验收阅读知识，再逐步操作。互动授课时用户说“继续”，一次只执行一个可验证步骤。实际命令、结果、报错和自测另存为本目录的实验笔记。

## 全局请求链路

客户端 → 路由和参数校验 → 身份与权限依赖 → 业务逻辑 → PostgreSQL → 响应模型。部署课再加入 Nginx、Uvicorn 与健康检查。数据定义和迁移沿用 [数据库课程](../../SQLAIchemy-AIembic-skill/course-plan.md)。

## 第 1 课｜从页面定位 API

**目标与验收**　从设备详情页的一条 Network 请求写出方法、路径、请求参数、状态码和响应字段，并用模拟数据实现对应 API。存在的设备返回设备详情，不存在的设备返回 404。

**先知道**　`APIRouter` 把一组路由集中管理。Pydantic 响应模型限定对外字段。请求路径里的设备 ID 是整数时，字符串占位符无法通过参数校验。

1. 在集成 PowerShell 中准备项目环境。

   ```powershell
   Set-Location 'D:\myskills\FastAPI-skill'
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install fastapi uvicorn httpx pytest
   ```

   预期安装结束无错误，VS Code 选择 `.venv\Scripts\python.exe`。已有环境直接复用并核对版本。

2. 在编辑器中新建 `app.py`。

   ```python
   from fastapi import APIRouter, FastAPI, HTTPException
   from pydantic import BaseModel


   class DeviceOut(BaseModel):
       id: int
       code: str
       status: str


   devices = {1: DeviceOut(id=1, code="sensor-01", status="online")}
   router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


   @router.get("/{device_id}", response_model=DeviceOut)
   def get_device(device_id: int) -> DeviceOut:
       device = devices.get(device_id)
       if device is None:
           raise HTTPException(status_code=404, detail="Device not found")
       return device


   app = FastAPI()
   app.include_router(router)
   ```

3. 在集成 PowerShell 启动并用另一集成终端验证。

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
   ```

   ```powershell
   curl.exe -i http://127.0.0.1:8000/api/v1/devices/1
   curl.exe -i http://127.0.0.1:8000/api/v1/devices/999
   curl.exe -i http://127.0.0.1:8000/api/v1/devices/DEVICE_ID
   ```

   预期依次为 200、404、422。核对 200 响应字段是否与页面实际使用字段一致。

**自测**　`DEVICE_ID` 与整数 `999` 为什么进入不同的失败环节？

## 第 2 课｜校验、依赖和权限

**目标与验收**　模拟一个需要调用者身份的设备接口，分别验证合法请求、参数错误、未认证和权限不足。

**先知道**　参数校验处理输入结构，认证确认调用者，授权判断调用者能否访问资源。`Depends` 管理每请求依赖。仅隐藏页面按钮不能替代服务端权限检查。

1. 在 `app.py` 中增加调用者依赖。实验令牌仅用于本地，不作为生产鉴权方案。

   ```python
   from fastapi import Depends, Header


   def current_project(x_project_id: int | None = Header(default=None)) -> int:
       if x_project_id is None:
           raise HTTPException(status_code=401, detail="Missing project identity")
       return x_project_id
   ```

2. 给路由增加 `project_id: int = Depends(current_project)` 参数，并在返回前判断设备所属项目。模拟数据也加入 `project_id`，返回模型只公开页面需要的字段。无访问权时返回课程约定的 403。

3. 在 VS Code 集成 PowerShell 用 `curl.exe -i -H "X-Project-Id: 1" ...` 验证合法请求，再去掉 Header、改成无权项目、改成非法路径 ID。分别记录状态码、响应体以及哪个环节拒绝了请求。

**自测**　认证通过后仍返回 403，能否据此判断请求参数一定有效？

## 第 3 课｜接入 PostgreSQL

**目标与验收**　复用数据库课程的项目与设备模型，每请求创建并关闭 Session，冲突导入时返回 409 且项目和设备均不落库。

**先知道**　数据库结构由 Alembic 迁移建立。Session 表示一次工作单元，`flush()` 可取得 ID，但事务仍可回滚。数据库连接地址取决于 FastAPI 运行位置。

1. 在 VS Code 中核对数据库课程的 `models.py`、`settings.py`、迁移版本和连接配置。记录当前库名、schema 和 `alembic current`。避免在两个课程目录复制出相互独立的模型版本。
2. 在路由依赖中创建 Session，使用 `yield` 并在结束时关闭。把业务写入放在一个事务中，创建项目后 `flush()`，添加全部设备，最后只提交一次。
3. 从本机集成 PowerShell 启动 API，分别发唯一设备编码与重复编码请求。重复时核对 HTTP 409，再按项目业务编码查 PostgreSQL，项目与设备均应为零行。

**自测**　`flush()` 后已经得到项目 ID，为什么仍能撤销整个项目？

## 第 4 课｜分页与告警查询

**目标与验收**　设备分页和告警筛选对项目隔离、空结果、时间范围与稳定顺序给出可复验的响应。

**先知道**　列表和 `total` 应使用同一组过滤条件。固定数据集按 `created_at DESC, id DESC` 排序，仍需认识 OFFSET 在并发插入时可能漂移。告警时间范围使用带时区的半开区间 `[start, end)`。

1. 在编辑器中核对接口的项目、关键词、页码和页大小参数。限制页大小，构造项目存在但无设备、项目不存在和同一时刻创建多设备三组数据。
2. 在集成 PowerShell 请求第一页、最后一页、超出范围页和非法页大小，检查 `total`、`items`、排序及 422/404/200 的适用情况。
3. 对告警接口分别请求带状态与不带状态的同一时间窗口，核对边界时刻只落入相邻一个窗口。用 `EXPLAIN (ANALYZE, BUFFERS)` 对照数据库课程的复合索引计划。

**自测**　项目存在但设备为空，与项目 ID 根本不存在，应怎样区分响应？

## 第 5 课｜接口测试和依赖替换

**目标与验收**　用 `pytest` 和 `TestClient` 对正常、422、401/403、404、409 建立可重复的断言。写入测试使用独立数据库。

**先知道**　依赖覆盖可以替换测试身份及 Session。每条测试要清理覆盖状态。测试数据库要与开发库分开，并用迁移初始化结构。

1. 在 `tests/test_api.py` 创建 `TestClient(app)`，先断言第 1 课的 200、404、422。运行 `python -m pytest -q`，记录失败用例与实际响应。
2. 对身份依赖使用 `app.dependency_overrides`，在测试结束后执行 `app.dependency_overrides.clear()`。验证被允许与被拒绝项目。
3. 为数据库写入测试配置独立测试库，运行 Alembic 迁移。触发重复编码后同时断言 HTTP 409 与数据库中不存在半批记录。

**自测**　为什么只断言 409 状态码，不能证明事务实现正确？

## 第 6 课｜部署与排障

**目标与验收**　部署后业务接口可用；数据库断开时就绪检查失败；重建后旧业务数据仍能查询。

**先知道**　链路为客户端 → Nginx → Uvicorn/FastAPI → PostgreSQL。存活检查确认进程能响应轻量请求，就绪检查确认关键依赖可用。迁移与服务启动分别执行。

1. 在 VS Code 中画出 Compose 服务与端口映射，标明 API 的数据库连接地址、环境配置位置和 PostgreSQL 数据卷位置。检查 `docker compose config` 的解析结果。
2. 独立执行 `python -m alembic upgrade head`，再启动 API。逐层验证容器状态、Uvicorn 日志、内部健康接口、经 Nginx 的业务响应。
3. 在隔离实验中暂停数据库，分别调用存活和就绪接口。恢复数据库后重建容器，查原有设备数据。保存实际命令、响应、日志及恢复步骤。

**自测**　`systemctl` 或容器状态为 running，为什么仍需调用业务接口验收？

## 第 7 课｜接手综合演练

**目标与验收**　独立完成一项设备或告警接口变更，交付字段映射、迁移核对、测试和发布记录。

1. 从页面 Network 请求写清现状、目标字段、身份和项目边界。
2. 修改路由与模型，若结构变化则审查 Alembic 脚本，并在有历史数据的测试库升级。
3. 运行接口测试，手动验证正常、空结果、错误输入与权限边界。记录响应和数据库查询证据。
4. 写出新旧代码与数据库结构的兼容判断、发布顺序及回退验收。课程笔记保留实际遇到的报错和有效修复动作。

**自测**　应用回退到旧版本后，为什么还要单独核对迁移和关键数据？
