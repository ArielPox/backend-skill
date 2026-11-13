# 实验 06｜综合实践：部署留言板

## 总体梳理

### 1. 请求怎么走

```text
Windows 浏览器访问 127.0.0.1:8086
    ↓ Docker 端口映射
web 容器 · Nginx 监听 80
    ↓ proxy_pass http://app:8000
app 容器 · Gunicorn 监听 8000，Flask 处理留言
    ↓ PyMySQL 连接 db:3306，执行 SQL
db 容器 · MySQL
    ↓ 数据目录 /var/lib/mysql
mysql-data 命名卷
```

Compose 的 `ports` 负责从 Windows 的 `8086` 到 Nginx 的 `80`。Nginx 配置里的 `proxy_pass` 负责从 Nginx 到应用的 `8000`。打开首页时，Flask 用 `SELECT` 查留言。点击提交时，Flask 用 `INSERT` 写入并提交，然后让浏览器回到首页重新查询。

### 2. 服务怎么启动

`docker compose up -d --build` 根据 `compose.yaml` 组装三个服务。Dockerfile 把 `app.py` 和 `requirements.txt` 中的依赖打包进应用镜像。构建时由 `RUN` 安装依赖，容器启动时由 `CMD` 运行 Gunicorn。MySQL 通过健康检查后，Compose 才启动依赖它的应用。Nginx 使用现成镜像，并挂载 `nginx.conf` 来转发请求。

### 3. 数据存在哪里

MySQL 将数据写入挂载了 `mysql-data` 的 `/var/lib/mysql`。执行 `docker compose down` 后，命名卷会保留。再次执行 `docker compose up -d` 时，新 MySQL 容器挂载原卷，所以应用能查到旧留言。若用 `docker compose down -v`，这个卷会随项目一起删除，下次启动将初始化空库。

### 排错对照与复习

- 临时应用容器使用 `DB_HOST=localhost` 时，会尝试连接自身的 MySQL 端口，预期连接失败并返回 `HTTP 500`。使用 `DB_HOST=db` 时，Compose 网络把服务名解析到 MySQL 容器，预期返回 `HTTP 200`。Flask 测试客户端直接请求应用，测试范围是应用与数据库的连接。
- **复习题**　如果浏览器入口改成 `8090`，只需将 Compose 端口映射改为 `127.0.0.1:8090:80`。为什么 `app:8000`、`db:3306` 和 `mysql-data` 可以沿用？因为这次修改的是 Windows 入口，容器间的地址和卷挂载仍然有效。

## 任务与知识点

用 Dockerfile 打包 Flask 应用，用 Compose 编排 Nginx、Gunicorn/Flask 和 MySQL。提交留言后重建容器，验证数据保留。再用临时容器对照测试错误与正确的数据库地址。

| 链路 | 地址 | 用途 |
| --- | --- | --- |
| Windows 浏览器 → Nginx | 127.0.0.1:8086 → web:80 | Compose 发布 Nginx 的端口 |
| Nginx → 应用 | app:8000 | Nginx 通过 Compose 服务名转发请求 |
| 应用 → MySQL | db:3306 | PyMySQL 通过服务名连接数据库 |

容器中的 localhost 指向该容器自身。应用和数据库在同一个 Compose 网络里通信，无需向 Windows 发布各自的端口。

## 实验配置

实验目录为 D:\myskills\dockerskill\lab06-message-board。Windows 命令提示符中可用 cd /d 切换目录和盘符。

| 文件 | 内容 |
| --- | --- |
| app.py | Flask 处理 GET 和 POST。GET 用 SELECT 读取留言，POST 用参数化 INSERT 写入并提交。 |
| requirements.txt | Flask、PyMySQL[rsa] 和 gunicorn。PyMySQL 是数据库驱动，[rsa] 提供认证所需的额外依赖。 |
| Dockerfile | 基于 python:3.12-slim。RUN pip install 在构建时安装依赖，CMD 在容器启动时执行 Gunicorn 并监听 0.0.0.0:8000。先复制依赖清单再复制代码，便于复用安装层缓存。 |
| nginx.conf | 监听 80，用 proxy_pass http://app:8000 转发请求。Compose 通过只读绑定挂载将配置放到 /etc/nginx/conf.d/default.conf。 |
| compose.yaml | web 发布 8086，app 使用 build: . 构建镜像，db 使用 mysql:8.4 并把 mysql-data 挂到 /var/lib/mysql。 |

应用的 DB_NAME、DB_USER 和 DB_PASSWORD 要与 MySQL 初始化配置对应。DB_HOST 填 db。MySQL 健康检查通过 TCP 使用应用账户执行 SELECT 1。Compose 等 db 健康后再启动 app。健康检查中的双美元符号让环境变量在容器中展开。

## 启动与持久化验证

| 命令或操作 | 作用与预期结果 |
| --- | --- |
| `docker compose config --quiet` | 检查 Compose 配置。--quiet 省略展开后的配置。 |
| `docker compose up -d --build` | 构建应用镜像并启动服务。-d 在后台运行，--build 在启动前构建镜像。 |
| 打开 http://127.0.0.1:8086/ | 预期显示留言板。提交一条测试留言后，应出现在列表中。 |
| `docker compose down` | 停止并删除服务容器及默认网络，保留命名卷。 |
| `docker compose up -d` | 使用原配置重建容器，重新挂载已有的 mysql-data。 |
| 刷新留言板 | 原留言仍然显示时，即验证了数据持久化。 |

down 加 -v 会删除本项目声明的命名卷，下次启动会初始化空数据库。

## 排错练习

构建时曾在 FROM python:3.12-slim 处收到 EOF。日志显示 Docker 请求镜像站的镜像信息时连接提前结束。用 docker pull python:3.12-slim 单独检查基础镜像能否拉取，拉取成功后再重试构建。

下面两条命令分别测试错误和正确的数据库地址。run 创建临时应用容器，--rm 让它退出后自动删除，--no-deps 跳过启动依赖，-e 只覆盖这次运行的环境变量。python -c 运行引号中的代码，用 Flask 测试客户端请求首页。

```cmd
docker compose run --rm --no-deps -e DB_HOST=localhost app python -c "from app import app; print('HTTP', app.test_client().get('/').status_code)"
docker compose run --rm --no-deps app python -c "from app import app; print('HTTP', app.test_client().get('/').status_code)"
```

第一条预期在日志中看到连接 localhost 失败并返回 HTTP 500。第二条沿用 DB_HOST=db，预期返回 HTTP 200。这两条命令不修改 Compose 文件或正在运行的服务。

## 自测回顾

1. pip install 什么时候执行？Dockerfile 的 RUN 在构建阶段执行，Gunicorn 由 CMD 在容器启动时启动。
2. 浏览器访问 8086 后，Nginx 转发到哪里？Docker 先把流量映射到 Nginx 的 80，再由 Nginx 转发到 app:8000。
3. 留言写在哪里？MySQL 通过 /var/lib/mysql 写入 mysql-data 命名卷。
4. 应用的数据库地址为什么是 db？Compose 网络用服务名定位容器，localhost 会连接应用容器自身。
