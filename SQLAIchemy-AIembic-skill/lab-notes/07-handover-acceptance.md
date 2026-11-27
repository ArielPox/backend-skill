# 实验 07 阶段笔记：现有接口接手验收

## 环境与运行方式

项目目录为 D:\myskills\SQLAIchemy-AIembic-skill，主实验库 p29_lab。VS Code 选择项目 .venv，运行 c24-check_handover_baseline.py，再运行 c25-run_api.py。服务地址 http://127.0.0.1:8000，文档地址 http://127.0.0.1:8000/docs。接口检查期间保持服务运行。

用户发送 1 表示当前运行结果符合教学预期。下表各项均已获得该确认，记录数量等未逐项提供的具体数值按实际数据库为准。

## FastAPI 如何连接数据库并实现四个接口

本节按当前项目代码讲解。阅读顺序是 settings.py → models.py → api.py / import_devices.py → c25-run_api.py。以下代码摘自当前文件，讲解对应这份实现。

### 先看一条完整的请求链路

~~~mermaid
flowchart TD
    A["浏览器 /docs 或 HTTP 客户端"] --> B["Uvicorn 接收请求，端口 8000"]
    B --> C["FastAPI 按请求方法和路径找到函数"]
    C --> D["解析并校验路径、查询参数或 JSON 请求体"]
    D --> E["接口函数 / import_project"]
    E --> F["SQLAlchemy Session 执行查询或写入"]
    F --> G["Engine 获取连接，psycopg 驱动发送 SQL"]
    G --> H["127.0.0.1:55432"]
    H --> I["Docker 映射至 PostgreSQL 容器端口 5432"]
    I --> J["p29_lab 中的业务表"]
    J --> K["结果经 Session 返回，函数构造字典或列表"]
    K --> L["FastAPI 编码为 JSON 并返回 HTTP 响应"]
~~~

浏览器访问 8000 上的 API 服务。应用连接数据库时使用 DATABASE_URL 中的 55432。在 Compose 网络内，其他容器通常通过服务名 db 和容器端口 5432 访问 PostgreSQL。

### 1. settings.py 从哪里取得数据库地址

当前配置加载代码如下。

~~~python
import os
from pathlib import Path

from dotenv import load_dotenv


# 按本文件的位置查找配置，支持从 VS Code 的不同工作目录运行。
# 已在终端设置的变量优先，方便临时切换到复现库。
load_dotenv(Path(__file__).resolve().parent / "local.env", override=False)
DATABASE_URL = os.environ["DATABASE_URL"]
~~~

load_dotenv 使用 settings.py 自身所在目录定位 local.env，因此在 VS Code 从其他工作目录启动脚本时，也能找到配置文件。override=False 表示已经存在的进程环境变量优先，这也是 c16 之后的实验能够通过子进程环境切换数据库的原因。

连接字符串的结构可以写成下面这样。密码位置使用占位符。

~~~text
postgresql+psycopg://p29:<数据库密码>@127.0.0.1:55432/p29_lab
~~~

| 部分 | 当前含义 |
|---|---|
| postgresql | 数据库类型 |
| psycopg | Python PostgreSQL 驱动 |
| p29 | 数据库用户名 |
| 127.0.0.1:55432 | 本机访问数据库的地址和映射端口 |
| p29_lab | 目标数据库名 |

os.environ["DATABASE_URL"] 要求该配置存在。缺失时会出现 KeyError。修改配置后重新启动应用进程，才会重新读取模块中的配置值。

### 2. Engine、Session 与模型如何配合

api.py 创建应用对象和数据库引擎。

~~~python
app = FastAPI()
engine = create_engine(DATABASE_URL)
~~~

Engine 管理数据库连接及连接池。create_engine 配置引擎，实际数据库连接通常在首次执行数据库操作、获取连接时建立。应用启动成功后，还需要通过数据库查询验收连接是否可用。

models.py 中的 Project、Device、Alarm 定义表名、字段、外键和 ORM 关系。已有表结构通过 Alembic 迁移创建和变更。

三个 GET 接口使用 api.py 中的 engine，每次处理请求时各自创建 Session。下面是项目树接口中的查询方式。

~~~python
with Session(engine) as session:
    projects = session.scalars(stmt).all()
~~~

- Session 管理本次数据库交互及 ORM 对象。
- select(...) 构造查询语句，执行发生在 session.scalars、session.scalar、session.get 等调用时。
- scalars(...).all() 收集查询结果第一列；select(Project) 的第一列是 Project ORM 实例。
- 查询接口在 with 块内将 ORM 对象转换成字典和列表。退出块时 Session 关闭，关联连接资源释放或归还连接池。
- Python 返回的列表和字典由 FastAPI 编码成 JSON，datetime 也会被转换成可传输的时间表示。

当前 POST 接口调用 import_devices.py 的 import_project，该函数内部会创建自己的 Engine 和 Session。它与三个 GET 接口共享 DATABASE_URL 配置。这里按当前代码记录连接创建的位置。

### 3. c25 如何启动服务，装饰器如何注册接口

启动脚本如下。

~~~python
import uvicorn

from api import app


if __name__ == "__main__":
    # 直接加载项目的 FastAPI 应用。
    # 本机浏览器通过 127.0.0.1:8000 访问。
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
~~~

from api import app 会执行 api.py 的模块初始化，创建 app、engine，并通过装饰器注册下面四个路由。随后 uvicorn.run 启动本机 HTTP 服务。

| 请求方法和路径 | 对应函数 | 参数来源 | 主要返回值 |
|---|---|---|---|
| POST /projects/import | import_project_endpoint | JSON 请求体 | 新建项目编码 |
| GET /projects/tree | project_tree | 无参数 | 项目与设备树 |
| GET /api/v1/projects/{project_id}/devices | list_project_devices | 路径 project_id；查询 page、page_size、q | total 和当前页 items |
| GET /api/v1/devices/{device_id}/alarms | list_device_alarms | 路径 device_id；查询 start、end、status | 告警 items |

例如 @app.get("/projects/tree") 将 GET 请求与紧随其后的函数绑定。POST 请求体通过 Pydantic 模型解析，路径里的变量通过函数参数接收，其余简单类型参数在这些 GET 接口中从查询字符串取得。

在 /docs 点击 Execute 会发送一次实际 HTTP 请求。当前代码采用同步 def 接口函数和 SQLAlchemy 同步 Session。

### 4. 接口一，导入项目与设备

下面给出一次请求示例。

~~~json
{
  "project_code": "DEMO-NEW-PROJECT",
  "device_codes": ["sensor-01", "sensor-02"]
}
~~~

同一个示例再次执行前，选择新的项目编码。项目编码具有唯一约束。

请求体模型及接口函数如下。

~~~python
class ProjectImport(BaseModel):
    project_code: str
    device_codes: list[str]


@app.post("/projects/import", status_code=status.HTTP_201_CREATED)
def import_project_endpoint(payload: ProjectImport):
    try:
        import_project(payload.project_code, payload.device_codes)
    except IntegrityError as exc:
        error = exc.orig
        if (
            isinstance(error, UniqueViolation)
            and error.diag.constraint_name == "uq_devices_project_id_code"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device codes must be unique within a project.",
            ) from exc
        raise

    return {"project_code": payload.project_code}
~~~

ProjectImport 要求请求体包含 project_code 和 device_codes，设备编码为字符串列表。请求体解析或校验失败时，FastAPI 返回 422。

装饰器中的 status_code 设置正常创建的响应为 201。接口把通过校验的数据交给 import_project，具体写入逻辑如下。

~~~python
def import_project(project_code: str, device_codes: list[str]) -> None:
    engine = create_engine(DATABASE_URL)

    with Session(engine) as session, session.begin():
        project = Project(code=project_code, name=project_code)
        session.add(project)
        session.flush()

        session.add_all(
            [
                Device(project_id=project.id, code=code, name=code)
                for code in device_codes
            ]
        )
~~~

~~~mermaid
flowchart TD
    A["创建 Project 对象并 add"] --> B["flush 写入项目，取得 project.id"]
    B --> C["使用 project.id 创建 Device 对象并 add_all"]
    C --> D{"退出 session.begin 时提交是否成功"}
    D -->|成功| E["项目和设备一起提交，接口返回 201"]
    D -->|唯一约束冲突| F["事务回滚"]
    F --> G["接口检查具体约束名，符合设备编码冲突时返回 409"]
~~~

flush 让项目 INSERT 执行并取得生成的 ID。事务仍处于提交前的状态，后续设备写入失败时，项目写入可以一起回滚。add_all 将设备加入 Session，待 flush 或提交时发送写入。

session.begin() 正常退出时提交，异常退出时回滚。这里的 with Session(engine) 还负责关闭 Session。

接口只将 psycopg UniqueViolation 且约束名为 uq_devices_project_id_code 的错误转换成 409。该约束保证同一项目内设备编码唯一。项目 code 重复等其他 IntegrityError 会继续抛出，当前代码没有为这些错误单独定义 409 响应。

### 5. 接口二，查询项目树

当前函数如下。

~~~python
@app.get("/projects/tree")
def project_tree():
    stmt = select(Project).options(selectinload(Project.devices)).order_by(Project.id)

    with Session(engine) as session:
        projects = session.scalars(stmt).all()
        return [
            {
                "code": project.code,
                "devices": [
                    {"code": device.code}
                    for device in sorted(project.devices, key=lambda device: device.id)
                ],
            }
            for project in projects
        ]
~~~

查询分为三个动作。

1. select(Project).order_by(Project.id) 选择项目并按 ID 排序。
2. selectinload(Project.devices) 批量加载关联设备，避免在遍历每个项目时分别触发一次设备查询。项目数量较多时，关联加载可能分批执行。
3. 在 Session 内读取 project.devices，按设备 ID 排序，再构造返回列表。

Project.devices 的 relationship 通过 Device.project_id 对应 projects.id。没有设备的项目，其 devices 为 []，正常返回 200。

返回数据的结构如下。

~~~json
[
  {
    "code": "A",
    "devices": [
      {"code": "sensor-01"},
      {"code": "sensor-02"}
    ]
  }
]
~~~

### 6. 接口三，设备分页与关键词筛选

下面给出一次请求示例。

~~~text
GET /api/v1/projects/1/devices?page=2&page_size=1&q=SENSOR
~~~

当前函数如下。

~~~python
@app.get("/api/v1/projects/{project_id}/devices")
def list_project_devices(
    project_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=50),
):
    with Session(engine) as session:
        if session.get(Project, project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        filters = [Device.project_id == project_id]
        keyword = q.strip() if q else ""
        if keyword:
            filters.append(Device.code.icontains(keyword, autoescape=True))
        total = session.scalar(select(func.count()).select_from(Device).where(*filters))

        stmt = (
            select(Device)
            .where(*filters)
            .order_by(Device.created_at.desc(), Device.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        devices = session.scalars(stmt).all()
        return {
            "total": total,
            "items": [
                {"id": device.id, "code": device.code, "created_at": device.created_at}
                for device in devices
            ],
        }
~~~

函数按下面的顺序处理请求。

1. project_id: int 校验路径参数类型；page、page_size 的 Query 声明范围，q 限制长度。
2. session.get(Project, project_id) 按主键查项目，缺失时主动抛出 404。
3. filters 首先限制项目归属。q 去掉两端空白后，使用 icontains 做不区分大小写的包含匹配；autoescape=True 处理关键词中的通配字符。
4. count 查询与设备列表复用同一份 filters，得到匹配设备总数 total。
5. created_at DESC、id DESC 提供时间加唯一 ID 的稳定排序。
6. offset=(page-1)*page_size 计算跳过多少条，limit 控制本页数量。
7. 返回 total 与 items。项目存在但无匹配设备时，结果为 200、total=0、items=[]。

count 和列表是两次查询。当前验收使用稳定的实验数据；并发数据变化时还需结合事务隔离级别讨论跨语句的一致性。

### 7. 接口四，按设备查询告警

下面给出一次请求示例。

~~~text
GET /api/v1/devices/1/alarms?start=2026-01-01T00:00:00Z&end=2026-01-08T00:00:00Z&status=open
~~~

当前函数如下。

~~~python
@app.get("/api/v1/devices/{device_id}/alarms")
def list_device_alarms(
    device_id: int,
    start: datetime,
    end: datetime,
    status: Literal["open", "closed"] | None = None,
):
    # 要求请求明确提供时区，避免本地时间产生歧义。
    if start.utcoffset() is None or end.utcoffset() is None:
        raise HTTPException(
            status_code=422,
            detail="start and end must include a timezone.",
        )

    if start >= end:
        raise HTTPException(
            status_code=422,
            detail="start must be earlier than end.",
        )

    with Session(engine) as session:
        if session.get(Device, device_id) is None:
            raise HTTPException(status_code=404, detail="Device not found.")

        # 半开区间让相邻时间段在边界处不会重复包含同一条告警。
        filters = [
            Alarm.device_id == device_id,
            Alarm.occurred_at >= start,
            Alarm.occurred_at < end,
        ]
        if status is not None:
            filters.append(Alarm.status == status)

        stmt = (
            select(Alarm)
            .where(*filters)
            .order_by(Alarm.occurred_at.desc(), Alarm.id.desc())
            .limit(50)
        )
        alarms = session.scalars(stmt).all()

        # 在 Session 关闭前，将结果转换成响应数据。
        return {
            "items": [
                {
                    "id": alarm.id,
                    "device_id": alarm.device_id,
                    "status": alarm.status,
                    "occurred_at": alarm.occurred_at,
                    "message": alarm.message,
                }
                for alarm in alarms
            ]
        }
~~~

函数按下面的顺序处理请求。

1. FastAPI 将 start、end 解析为 datetime。Literal 限定 status 为 open 或 closed，省略时为 None。
2. 函数检查两个时间都带时区，并要求 start < end，失败返回 422。
3. 按主键检查设备是否存在，缺失返回 404。
4. 查询始终包含设备 ID，以及 occurred_at >= start、occurred_at < end 的半开时间区间。
5. 提供 status 时增加状态条件，省略时查询所有状态。
6. 按 occurred_at DESC、id DESC 排序，最多取 50 条。当前接口提供有上限的列表。
7. 在 Session 关闭前构造包含 id、device_id、status、occurred_at、message 的响应。

半开区间让相邻时间段能够衔接，例如上一段以 01-08 00:00 为结束，下一段以同一时刻为开始，该时刻的记录归到下一段。

### 8. 从 HTTP 状态码定位代码环节

| 状态码 | 本项目中的来源 | 示例 |
|---|---|---|
| 200 | GET 查询成功 | 非空结果、空设备列表 |
| 201 | 导入函数成功提交 | 项目和设备创建成功 |
| 422 | 参数解析、声明约束或函数内时间校验 | page=0、status=pending、时间缺少时区 |
| 404 | 函数查询后发现资源缺失 | 项目或设备不存在 |
| 409 | 指定设备唯一约束冲突，经接口转换 | 同一项目导入重复设备编码 |
| 500 | 未被接口转换处理的服务端异常 | 当前代码中某些其他数据库异常 |

新增接口时，可按已有实现的顺序完成路由和参数定义、参数与资源校验、Session 内数据库操作、事务边界与错误转换、响应构造，最后通过 /docs 或 HTTP 客户端验收。

### 9. 自测与参考答案

- 请求访问 8000，数据库连接访问哪个端口？当前本机应用使用 DATABASE_URL 的 55432，经 Docker 映射到容器 5432。
- 为什么 Session 中取得 project.id 后设备写入失败，项目仍能撤销？flush 已发送 INSERT，但同一事务尚未提交。
- 为什么没有匹配设备也能返回 200？项目存在，设备查询正常完成，结果数量为零。
- 省略告警 status 参数会怎样？省略状态筛选，仍按设备和时间过滤。
- 修改模型后，API 能自动创建新字段吗？当前项目由 Alembic 迁移负责数据库结构变更，发布时需要完成对应升级。

## 已完成验收

| 项目 | 操作 | 确认结果 |
|---|---|---|
| 基础状态 | 运行 c24 | 主库 p29_lab，版本 c5441c214269；项目、设备、告警表及关键字段齐全，记录数均大于零 |
| 服务启动 | 运行 c25，打开 /docs | 四个课程接口均可见 |
| 项目树 | GET /projects/tree | 200，项目包含设备列表，无设备时为空列表 |
| 分页筛选 | 项目 1，page_size=1，q=SENSOR，依次 page=1、2 | 200；匹配编码包含 sensor；total 口径一致；分页符合数量和稳定排序规则 |
| 分页错误 | page=0；page_size=101；恢复合法参数 | 422、422、200；错误位置分别指向 page 和 page_size |
| 告警查询 | 设备 1，UTC 2026-01-01 至 2026-01-08，status=open | 200，非空且最多 50 条，设备及状态符合，时间为左闭右开，时间与 ID 降序 |
| 告警时间校验 | start 缺少时区；开始晚于结束；恢复有效范围 | 422、422、200 |
| 导入冲突 | 项目 ACCEPT-TX-20261127-A，重复 sensor-01 | 409，提示同项目设备编码需唯一 |
| 同编码重试 | 同项目改用 sensor-01 和 sensor-02 | 201；项目树显示恰好两台设备，首次项目写入已随事务回滚 |
| 无匹配设备 | 项目 1，q=NO-MATCH-20261127 | 200，total=0，items=[] |
| 不存在项目 | 项目 ID 2147483647 | 404，Project not found. |
| 非法告警状态 | status=pending，其余为有效告警参数 | 422，错误位置 query/status，允许值 open、closed |

## 关键知识与自测

page 的 ge=1 限制最小页码，page_size 的 ge=1、le=100 限制每页数量。total 使用与当前列表一致的项目和关键词过滤条件。

告警时间必须带时区，start 小于 end。status 的 Literal 限定 open、closed，省略参数时查询两种状态。

项目存在且没有设备时应返回 200 与空列表。用户回答 200，正确。项目本身不存在时返回 404。

重复设备编码违反唯一约束，项目与设备在同一事务内回滚。同一项目编码使用合法设备重试成功，并通过项目树核对结果。完整复做此组写入实验时使用新的项目编码。

## 本轮错误对照

422、404 和 409 均为主动构造的预期响应。时间错误信息分别为 start and end must include a timezone. 和 start must be earlier than end.。当前阶段没有收到新的非预期故障报告。

## 后续任务

按课程计划补齐 users、roles、qa_sessions、mail_accounts 最小模型和迁移，记录关系、唯一约束、敏感字段来源。随后在隔离环境演练连错库、漏跑迁移和重复种子数据，补齐接手验收记录。

本阶段完成现有接口验收，第 7 课后续内容继续推进。
