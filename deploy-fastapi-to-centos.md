# FastAPI 本地项目部署到 CentOS 7：实操指南

本文整理自一次已验证成功的部署：Windows 本地开发，将代码上传至已有其他服务的 CentOS 7.9 服务器，使用独立 Python 环境和 systemd 运行，通过 SSH 隧道访问。

## 1. 适用范围与部署结果

- 本地：Windows、PowerShell、Python 3.13。
- 服务器：CentOS 7.9，系统已有 Python 2.7.5 和 Python 3.6.8。
- 为新项目单独安装 Python；不替换系统 Python，不修改其他后端的依赖。
- 新建专用服务账号，使用 systemd 管理后台运行、异常重启和开机启动。
- 服务监听 `127.0.0.1:8000`，通过 SSH 隧道访问；本指南不配置公网 HTTP、域名或 HTTPS。

实际验证结果：服务为 `active (running)`，`/health` 返回 `{"status":"ok"}`，开机启动设置成功。

> CentOS 7 已于 2024 年 6 月 30 日结束维护。本流程用于必须保留现有服务器的情况，不代表解决了旧系统的安全维护问题。新部署环境优先选择仍受支持的系统。不要为迁就旧系统将真实项目降级至 Python 3.6。

## 2. 先确定项目参数

下文使用示例值，真实项目需要统一替换。

| 参数 | 示例 | 说明 |
|---|---|---|
| 本地目录 | `D:\Amyproject\后端部署测试` | 代码所在目录 |
| 服务器地址 | `服务器公网IP` | 替换为实际地址 |
| SSH 用户 | `root` | 本次实际使用的部署账号；应用运行另用普通账号 |
| 部署目录 | `/opt/fastapi-demo` | 必须与其他项目分开 |
| 服务名和运行账号 | `fastapi-demo` | 选择未被其他项目使用的名称 |
| Python 版本 | `3.13` | 与项目支持的版本一致 |
| 应用入口 | `main:app` | `main.py` 中的 `app` 对象 |
| 服务端口 | `8000` | 启动前确认空闲 |
| 本地隧道端口 | `18000` | 与本地开发使用的 8000 区分 |

如果入口是 `app/main.py` 中的 `app`，一般改为 `app.main:app`，并从项目根目录启动。还需确认真实项目的环境变量、数据库、外部服务、静态文件和迁移要求。

## 3. 创建并验证本地项目

示例目录：

```text
后端部署测试/
├── main.py
├── requirements.txt
├── .gitignore
└── .venv/
```

`main.py`：

```python
from fastapi import FastAPI

app = FastAPI(title="我的第一个后端", version="1.0.0")


@app.get("/")
def root():
    return {"message": "FastAPI 后端运行成功！"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/hello")
def hello(name: str = "世界"):
    return {"message": f"你好，{name}！"}
```

本次示例的 `requirements.txt`：

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
```

> 以上是示例版本范围，每次安装可能解析出不同版本。真实项目应使用项目已经验证过的依赖锁定文件或固定版本，并验证 Linux/Python 目标环境。不要将包含 Windows 专用依赖的 `pip freeze` 结果不加检查地当作 Linux 部署清单。

`.gitignore`：

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
```

**执行位置：本地 PowerShell。**

```powershell
cd D:\Amyproject\后端部署测试
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

依次打开：

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/hello?name=Amy
- http://127.0.0.1:8000/docs

确认接口正常后再部署。`--reload` 仅用于开发，服务器后台配置中不使用。

## 4. 登录并检查服务器

**执行位置：本地 PowerShell。**

```powershell
ssh root@服务器公网IP
```

**以下命令在登录后的服务器终端执行，均为只读检查。**

```bash
cat /etc/centos-release
python --version
python3 --version
whoami

for cmd in python3.10 python3.11 python3.12 python3.13; do
    command -v "$cmd" && "$cmd" --version
done

command -v docker
systemctl is-active docker
ss -lntp
free -h
df -h /opt
```

检查目标端口：

```bash
ss -lntp 'sport = :8000'
```

只有表头表示当前没有 TCP 监听记录。如果已占用，为新项目换端口，不要结束已有服务的进程。

本次服务器没有找到可用的新 Python 或 Docker，资源充足，因此选择项目目录内的独立 Python。

> 虚拟环境只隔离 Python 依赖，不隔离 CPU、内存、磁盘或网络。资源仍与其他后端共享，不能承诺完全零影响。下文为新服务设置 CPU 和内存上限。

## 5. 安装项目专用 Python

**执行位置：服务器终端。以下是首次安装步骤，不要对已有部署反复执行。**

创建新目录：

```bash
mkdir /opt/fastapi-demo
cd /opt/fastapi-demo
```

如果提示目录已存在，先检查内容和用途，避免覆盖其他项目。

下载 uv 安装脚本，并把 uv 安装在项目目录：

```bash
curl -fL --connect-timeout 20 https://astral.sh/uv/install.sh -o uv-install.sh
UV_UNMANAGED_INSTALL=/opt/fastapi-demo/tools sh uv-install.sh
/opt/fastapi-demo/tools/uv --version
```

逐条执行，下载失败时不要继续。`UV_UNMANAGED_INSTALL` 指定安装位置，并避免安装器修改 shell 启动配置。组织有软件来源审核要求时，先审核安装脚本并采用批准的固定版本。

指定 Python 和缓存目录，再创建虚拟环境：

```bash
export UV_PYTHON_INSTALL_DIR=/opt/fastapi-demo/python
export UV_CACHE_DIR=/opt/fastapi-demo/cache

/opt/fastapi-demo/tools/uv venv --python 3.13 /opt/fastapi-demo/.venv
/opt/fastapi-demo/.venv/bin/python --version
```

uv 会在缺少指定版本时下载 Python。本次实际安装并验证成功的是 Python 3.13.18；未来下载的补丁版本可能不同。

注意：

- 不替换 `/usr/bin/python` 或 `/usr/bin/python3`，不修改它们的软链接。
- 后续用完整路径调用项目 Python，避免误装依赖到系统环境。
- `.venv` 可能引用 `/opt/fastapi-demo/python` 中的解释器，不要在部署后删除该目录。
- `export` 只对当前终端及其子进程生效；重新安装环境时需要重新设置。systemd 启动不依赖这些变量。

## 6. 上传本地项目

**执行位置：本地电脑新开的 PowerShell，不是在服务器终端。**

```powershell
cd D:\Amyproject\后端部署测试
scp .\main.py .\requirements.txt root@服务器公网IP:/opt/fastapi-demo/
```

如果 SSH 使用自定义端口，`ssh` 用小写 `-p`，`scp` 用大写 `-P`：

```powershell
scp -P 你的SSH端口 .\main.py .\requirements.txt root@服务器公网IP:/opt/fastapi-demo/
```

真实项目应上传完整的运行源码、模板、静态资源和必要配置。不要只上传入口文件。例如源码位于 `app` 目录时：

```powershell
scp -r .\app root@服务器公网IP:/opt/fastapi-demo/
```

不上传本地 `.venv`、缓存、`.git` 或不必要的数据。Windows 虚拟环境不能直接用于 Linux。密钥和密码单独安全配置，不写入源码。

## 7. 安装依赖并手动验证

**执行位置：服务器终端。**

```bash
cd /opt/fastapi-demo
ls -l main.py requirements.txt

UV_CACHE_DIR=/opt/fastapi-demo/cache /opt/fastapi-demo/tools/uv pip install --python /opt/fastapi-demo/.venv/bin/python -r /opt/fastapi-demo/requirements.txt
```

依赖安装成功后启动：

```bash
/opt/fastapi-demo/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

看到 `Application startup complete` 和 `Uvicorn running on http://127.0.0.1:8000` 后，保持窗口开启。

另开 SSH 窗口登录同一台服务器，执行：

```bash
curl --fail --show-error http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

示例健康检查只证明 HTTP 应用能响应，不代表数据库或其他依赖也正常。真实项目还应验证必要的业务接口和依赖连接。

## 8. 用 SSH 隧道从电脑访问

**执行位置：本地新开的 PowerShell。**

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:18000:127.0.0.1:8000 root@服务器公网IP
```

输入密码后没有新输出、终端保持等待是正常的。此命令需要服务器允许 SSH 端口转发。

在本地浏览器访问：

```text
http://127.0.0.1:18000/docs
```

访问路径：

```text
本地浏览器 → 本地 18000 端口 → SSH 隧道 → 服务器 127.0.0.1:8000
```

- 不需要开放服务器公网 8000 端口。
- 隧道窗口关闭后，本地 18000 入口消失。
- 如果本地 18000 已占用，改用 18001 等空闲端口，并同步修改浏览器地址。
- 服务器的 `127.0.0.1` 和本地电脑的 `127.0.0.1` 指向各自机器，不能混淆。

## 9. 创建专用服务账号

此时保持手动运行 Uvicorn 的窗口和隧道窗口开启，另开 SSH 窗口完成配置。

**执行位置：服务器终端。**

```bash
useradd --system --user-group --no-create-home --shell /sbin/nologin fastapi-demo
```

若用户已存在，先核实用途，不要直接复用其他服务账号。

验证账号能够读取项目并执行解释器：

```bash
cd /opt/fastapi-demo
runuser -u fastapi-demo -- /opt/fastapi-demo/.venv/bin/python -c "from main import app; print('OK')"
```

预期输出 `OK`。真实项目导入时可能初始化外部资源，应先准备好配置并了解启动行为。

如果出现权限错误，检查具体路径的所有者、读取和目录遍历权限，不要直接 `chmod 777`，也不要修改其他项目目录。示例应用不需要写入源码目录；真实项目的上传或数据文件应使用专门的可写目录，仅授权给该服务账号。

## 10. 配置 systemd 后台服务

### 10.1 确认服务名未被占用

```bash
systemctl cat fastapi-demo.service
ls /etc/systemd/system/fastapi-demo.service
```

首次部署预期提示没有对应单元或文件。如果已有配置，先核实用途，不覆盖其他服务。

### 10.2 创建配置

完整复制以下内容，包含最后一行 `EOF`：

```bash
cat > /etc/systemd/system/fastapi-demo.service <<'EOF'
[Unit]
Description=FastAPI Demo
After=network.target

[Service]
Type=simple
User=fastapi-demo
Group=fastapi-demo
WorkingDirectory=/opt/fastapi-demo
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=/opt/fastapi-demo/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=on-failure
RestartSec=5
MemoryAccounting=true
MemoryLimit=512M
CPUAccounting=true
CPUQuota=50%
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

配置含义：

| 配置 | 作用 |
|---|---|
| `User` / `Group` | 使用专用普通账号运行应用 |
| `WorkingDirectory` | 指定项目工作目录 |
| `ExecStart` | 使用项目 Python 启动，真实项目需修改入口 |
| `--workers 1` | 先使用一个进程 |
| `Restart=on-failure` | 异常退出后重启；手动 stop 不会触发重启 |
| `RestartSec=5` | 重启前等待 5 秒 |
| `MemoryLimit=512M` | 内存上限；超限可能导致进程被终止 |
| `CPUQuota=50%` | 约半个 CPU 核心的时间配额，不是整机 CPU 的一半 |
| `PrivateTmp=true` | 使用独立临时目录视图 |

这些限额适合当前简单示例。真实项目应根据启动峰值和负载测试调整；多个 worker、模型加载或大文件处理可能需要更多内存。该配置采用本次 CentOS 7 使用的 `MemoryLimit` 指令，迁移新系统时应按目标 systemd 文档复核。

### 10.3 真实项目的环境变量（按需）

systemd 不会自动继承你 SSH 终端中的 `export`，也不会自动读取项目 `.env`。

可以在 `[Service]` 中加入：

```ini
EnvironmentFile=/etc/fastapi-demo.env
```

对应文件每行使用 `KEY=value`，不写 `export`，限制文件读取权限，例如由 root 持有、权限 `600`。本例是系统级服务，systemd 可读取该文件后将变量传给应用。不要把含密钥的文件提交到 Git 或粘贴到排障截图中。

本示例无需环境文件，因此上面的基础配置没有包含这一行。真实项目还应单独规划数据库迁移；不要把可能破坏数据的迁移当作普通启动步骤反复执行。

### 10.4 从手动运行切换到后台运行

1. 回到显示 Uvicorn 日志的窗口，按 `Ctrl+C` 停止本项目的手动进程。
2. 保持 SSH 隧道窗口开启。
3. 在配置窗口执行：

```bash
systemctl daemon-reload
systemctl start fastapi-demo
systemctl status fastapi-demo --no-pager -l
curl --fail --show-error http://127.0.0.1:8000/health
```

`daemon-reload` 重新读取单元配置，不会重启其他后端。注意 `-l` 是小写字母 L，不是数字 1。

确认 `active (running)` 且健康检查成功后设置开机启动：

```bash
systemctl enable fastapi-demo
systemctl is-enabled fastapi-demo
```

预期输出 `enabled`。无需为验证开机启动而重启这台运行其他服务的服务器。

现在普通 SSH 登录窗口可以关闭，后端继续运行；通过本地 18000 访问仍需保持 SSH 隧道。

## 11. 日常管理

以下命令仅针对新服务：

```bash
# 查看服务状态
systemctl status fastapi-demo --no-pager -l

# 查看最近日志
journalctl -u fastapi-demo -n 50 --no-pager

# 持续查看日志；Ctrl+C 只退出日志查看
journalctl -u fastapi-demo -f

# 重启、停止、启动
systemctl restart fastapi-demo
systemctl stop fastapi-demo
systemctl start fastapi-demo

# 取消开机启动（不会立即停止当前进程）
systemctl disable fastapi-demo

# 查看配置的资源限额
systemctl show fastapi-demo -p MemoryLimit -p CPUQuotaPerSecUSec
```

服务日志由系统 journal 管理。需要长期审计时，应确认日志保留策略，避免假设所有历史日志都会永久保存。

## 12. 更新真实项目

### 12.1 分开管理代码、运行环境、配置和运行数据

分开管理的目的是：更新代码时，不覆盖生产配置、不删除用户文件，也不修改正在运行的旧版本依赖。通常用不同目录管理，不一定需要不同服务器。

以一个允许用户上传图片并处理图片的 FastAPI 项目为例：

| 类别 | 包含什么 | 发布时如何处理 |
|---|---|---|
| 代码 | 接口、业务逻辑、模板、静态资源、数据库迁移脚本 | 打包上传到新的版本目录 |
| 运行环境 | Python、FastAPI 和其他依赖 | 在服务器创建；每个版本可使用独立虚拟环境 |
| 配置 | 数据库地址、密码、API 密钥、上传目录路径 | 存放在代码包外，按环境单独配置 |
| 运行数据 | 用户上传文件、生成结果、数据库记录 | 独立持久保存和备份，不随发布覆盖 |

下面是大型项目可采用的目录结构，`my-backend` 是示例名称。它属于后续改造方案，不是本次 `fastapi-demo` 已经创建的目录：

```text
/opt/my-backend/
├── python/                  # 独立 Python，供虚拟环境引用
├── tools/                   # uv 等工具
├── packages/                # 上传的源码压缩包
├── releases/
│   ├── v1/
│   │   ├── app/
│   │   ├── migrations/
│   │   ├── requirements.txt
│   │   └── .venv/           # v1 在服务器上创建的依赖环境
│   └── v2/
│       ├── app/
│       ├── migrations/
│       ├── requirements.txt
│       └── .venv/           # v2 在服务器上创建的依赖环境
└── current -> releases/v2   # 软链接，指向当前版本

/etc/my-backend/
└── app.env                  # 生产配置，限制读取权限

/var/lib/my-backend/
├── uploads/                 # 持久化上传文件
└── results/                 # 持久化生成结果
```

**代码与运行环境：** 每次发布新增版本目录，保留上一版本。为 `v2` 安装依赖时不改变 `v1/.venv`。虚拟环境即使位于版本目录中，也不属于源码包，应在服务器的最终版本路径中创建，避免创建后搬迁导致路径失效。清理旧版本时还要保留被其他虚拟环境引用的共享 Python。

**配置：** 同一份代码可以在本地连接测试数据库，在服务器连接生产数据库，差异由环境变量决定。例如 `/etc/my-backend/app.env`：

```dotenv
APP_ENV=production
DATABASE_URL=实际数据库连接地址
UPLOAD_DIR=/var/lib/my-backend/uploads
API_KEY=实际密钥
```

systemd 的 `[Service]` 中通过下面的配置加载：

```ini
EnvironmentFile=/etc/my-backend/app.env
```

应用读取变量：

```python
import os

database_url = os.environ["DATABASE_URL"]
upload_dir = os.environ["UPLOAD_DIR"]
```

生产配置不放进源码压缩包或 Git。配置也需要备份和变更记录，并确认新旧代码对配置的兼容性。环境文件权限说明见第 10.3 节。

**运行数据：** 不要将用户上传文件保存到 `releases/v1/uploads` 这类版本目录，否则切换版本可能找不到文件，清理旧版本还可能删除数据。使用配置指定的绝对路径，让不同代码版本访问同一份持久数据。仅向服务账号授权必要数据目录的写入权限，源码和配置不必允许应用修改。

数据库迁移脚本属于代码，随版本发布；数据库记录属于运行数据，由数据库服务管理并单独备份。切回旧代码不会自动撤销数据库变化。日志可继续交给 journal 管理。

### 12.2 大项目打包上传

源码压缩包解决文件多、上传零散的问题；它不包含完整运行环境，也不等于 Docker 镜像。当前部署方式可以直接使用 `.tar.gz`，无需为此安装 Docker。

**执行位置：本地 PowerShell。** 进入真实项目根目录，按实际文件清单打包。例如：

```powershell
tar -czf ..\my-backend-v2.tar.gz app migrations templates static requirements.txt pyproject.toml
tar -tzf ..\my-backend-v2.tar.gz
```

以上文件或目录必须实际存在；删除不存在的名称，加入项目运行所需的其他文件。压缩包放在项目目录之外，避免把压缩包自身打进去。

不打包本地 `.venv`、`.git`、缓存、日志、生产密钥、数据库文件和用户上传数据。`templates`、`static` 中随代码发布的资源需要打包，用户运行时生成的文件则应单独保存。

**执行位置：服务器终端。** 确认目标属于本项目后，准备包目录和新的版本目录：

```bash
mkdir -p /opt/my-backend/packages /opt/my-backend/releases
mkdir /opt/my-backend/releases/v2
```

如果 `v2` 已存在，先核实内容，不向正在运行的版本直接解压覆盖。

**执行位置：本地 PowerShell。**

```powershell
scp ..\my-backend-v2.tar.gz root@服务器公网IP:/opt/my-backend/packages/
```

**执行位置：服务器终端。** 先查看包内路径，确认来自本项目且没有异常的绝对路径或 `..` 路径，再解压：

```bash
tar -tzf /opt/my-backend/packages/my-backend-v2.tar.gz
tar --no-same-owner -xzf /opt/my-backend/packages/my-backend-v2.tar.gz -C /opt/my-backend/releases/v2
```

解压完成后仍需要：在该版本目录创建虚拟环境、安装锁定依赖、配置权限与环境变量，并验证应用。不要直接照搬前面 `/opt/fastapi-demo/.venv` 的安装路径。

### 12.3 版本化发布与回滚顺序

```text
本地验证 → 打包源码 → 上传并解压到新版本目录
→ 为新版本创建环境、安装依赖 → 配置并验证
→ 停止本项目服务 → 切换版本入口 → 启动并检查
→ 保留旧版本用于回滚
```

采用 `current` 软链接时，systemd 的路径也需要一起改造。例如入口为 `app/main.py` 中的 `app` 时，相关配置是：

```ini
WorkingDirectory=/opt/my-backend/current
EnvironmentFile=/etc/my-backend/app.env
ExecStart=/opt/my-backend/current/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

这只是路径调整示例，不是完整服务文件；仍需配置实际服务账号和资源限制。端口需要重新检查。如果旧示例仍占用 8000，应选择其他空闲端口。改造前先确保配置文件、目录、账号权限和新版本环境已准备好。

软链接切换本身不会让正在运行的进程自动加载新代码。对当前单服务方案，安排短暂维护窗口，先停止本项目再切换，随后启动并检查；不要停止其他后端。如果只切换链接而未修改单元文件，通常不需要 `daemon-reload`。

新版本失败时，停止新进程、切回旧版本目录、确认配置和数据库仍兼容，再启动旧版本。保留旧源码及其匹配的 `.venv`，回滚才更可靠。用于预验证的应用如果会启动定时任务、消息消费者或执行写操作，应先隔离这些行为，避免与生产实例重复执行。

版本目录方便回滚，但并不自动提供零停机部署。不能停机的项目还需要多实例、健康检查和反向代理流量切换。

### 12.4 当前简单目录结构的更新方式

以下适用于前文已经部署的 `/opt/fastapi-demo`，与上面的版本目录方案择一使用。

首次部署和后续更新不同：更新时不要重新创建账号、覆盖无关配置或重建正在使用的虚拟环境。

对于可以接受短暂停机的小项目：

1. 保留当前已验证的代码版本、依赖清单和配置备份。
2. 将新版本上传到独立的暂存目录，先检查文件是否完整。
3. 安排维护窗口，执行 `systemctl stop fastapi-demo`。
4. 将审核后的新代码部署到项目目录；不要覆盖 `python`、`tools` 和 `.venv`，不要误删运行数据。
5. 如果依赖变化，使用该项目的 uv 命令安装已验证的新依赖。
6. 如果服务配置变化，执行 `systemctl daemon-reload`。
7. 执行 `systemctl start fastapi-demo`，检查状态、日志、健康检查和关键业务接口。

依赖安装命令：

```bash
UV_CACHE_DIR=/opt/fastapi-demo/cache /opt/fastapi-demo/tools/uv pip install --python /opt/fastapi-demo/.venv/bin/python -r /opt/fastapi-demo/requirements.txt
```

注意：`uv pip install -r` 不保证清除所有不再需要的包。严格可复现的部署应基于锁定依赖和新的虚拟环境验证。

更新失败时停止新版本，恢复已验证的代码和匹配依赖后再启动。仅恢复源码不一定能撤销依赖变化；数据库迁移也需要单独的备份和回退方案。

对于不能停机或需要可靠快速回滚的项目，应进一步采用版本化发布目录、每个版本独立环境及流量切换方案；本文的单进程部署不提供零停机更新。

## 13. 常见问题

| 现象 | 检查和处理 |
|---|---|
| `No module named uvicorn` | 依赖没有装进当前解释器；使用明确指定 `.venv/bin/python` 的安装命令 |
| 找不到 `requirements.txt` | 确认上传到正确目录，使用绝对路径检查 |
| `Could not import module` | 检查工作目录、源码完整性、入口名称和导入依赖 |
| `Address already in use` | 手动进程尚未停止或端口被其他服务占用；先确认进程归属，不批量杀进程 |
| `Permission denied` | 检查专用账号对项目、解释器和必要目录的权限；不要使用 `chmod 777` |
| `systemctl: invalid option -- '1'` | 将数字 `-1` 改为小写字母 `-l`，或省略该参数 |
| 服务启动后失败 | 执行 `journalctl -u fastapi-demo -n 50 --no-pager` 查看原因 |
| 下载超时或 TLS 错误 | 检查网络、系统时间和证书；不要通过关闭证书校验来解决 |
| `GLIBC` 或二进制兼容性报错 | 目标系统较旧；选择经验证的兼容构建，不要直接升级系统 glibc 影响其他服务 |
| 本地 18000 无法访问 | 检查隧道是否仍运行、本地端口是否冲突、服务器内部健康检查是否成功 |
| 公网 IP 加 8000 无法访问 | 当前只监听 `127.0.0.1`，属于预期行为 |
| 服务反复重启 | 检查日志、配置和内存限额，不要仅靠反复 restart |

如果权限看似正常仍被拒绝，检查 SELinux 审计记录和具体文件上下文；不要为排障直接全局关闭 SELinux。

## 14. 对外访问的边界

本流程最终提供的是“服务器后台常驻 + SSH 隧道访问”，适用于个人验证或受控运维访问。

如需让前端、手机或其他用户直接访问，仍需单独规划：

- 域名和 HTTPS。
- 反向代理到本地 FastAPI 端口。
- 云安全组及系统防火墙的最小必要放行。
- 接口鉴权、访问控制，以及是否公开 `/docs`。
- 跨域前端需要的 CORS 配置。

已有 Nginx 或网关的服务器，应先检查配置并确定独立路由，验证配置后再进行受控重载；不能覆盖现有站点。不要把监听改成 `0.0.0.0` 视为已经完成正式公网部署。

## 15. 完成检查清单

- [ ] 本地应用和关键接口验证通过。
- [ ] 服务器版本、端口和资源已检查。
- [ ] Python 和依赖位于项目独立目录，系统 Python 保持原样。
- [ ] 完整运行源码和必要配置已上传。
- [ ] 专用账号可以启动应用。
- [ ] 手动运行验证通过。
- [ ] systemd 状态为 `active (running)`。
- [ ] 健康检查和关键业务接口通过。
- [ ] `systemctl is-enabled fastapi-demo` 返回 `enabled`。
- [ ] 资源限制符合真实项目需求。
- [ ] 已了解查看日志、更新及回滚的方法。
- [ ] 明确当前仅通过 SSH 隧道访问，还是已另行配置正式公网入口。

## 参考资料

- [FastAPI：手动运行服务器](https://fastapi.tiangolo.com/deployment/manually/)
- [uv：安装目录与不修改 shell 配置](https://docs.astral.sh/uv/reference/installer/)
- [uv：创建虚拟环境](https://docs.astral.sh/uv/pip/environments/)
- [Red Hat Enterprise Linux 7：资源限制](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/resource_management_guide/sec-modifying_control_groups)
- [systemd：服务和重启行为](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- [CentOS Linux 生命周期](https://www.centos.org/centos-linux/)
