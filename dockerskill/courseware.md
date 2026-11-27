# Docker 动手实验课件

对应 [课程计划](./course-plan.md)。在 VS Code 打开 `D:\myskills\dockerskill`，使用集成 PowerShell 终端。互动时每次“继续”只执行下一项可验证操作。每课结束后记录实际命令、输出、故障和自测。


---

## 实验 01｜镜像与容器基础

### 任务目标

在 Windows 10 的 Docker Desktop（WSL2 后端）中运行 Nginx，从本机访问网页，并验证停止、重启和删除容器对文件改动的影响。

### 知识点

- **镜像**是由只读层组成的运行模板。标签可以表示版本或变体，例如 nginx:alpine。省略标签时默认用 latest，标签所指的镜像可以更新。
- **容器**由镜像创建。主进程退出时容器停止。-d 让 Docker 客户端在启动后返回终端，容器的运行时间取决于主进程。
- **端口映射**按“宿主机端口:容器端口”填写。8081:80 把访问本机 8081 的请求转到 Nginx 监听的 80。只供本机访问时，可写成 127.0.0.1:8081:80。
- **容器可写层**记录容器内普通文件的新增、修改和删除。stop/start 保留这层，rm 删除容器时会移除这层。同一镜像创建的新容器有自己的可写层。

### 实验操作

| 命令 | 参数与作用 |
| --- | --- |
| `docker pull nginx:alpine` | 拉取 nginx 镜像的 alpine 变体。本地已有时可以跳过。 |
| `docker images` | 列出本地镜像及其标签。 |
| `docker run -d --name lab1-nginx -p 8081:80 nginx:alpine` | 创建并启动容器。-d 后台运行，--name 指定名称，-p 发布端口。 |
| `docker ps` / `docker ps -a` | 查看运行中的容器。加 -a 也能看到已停止和仅创建的容器。 |
| `curl.exe -I http://localhost:8081` | -I 请求 HTTP 响应头，原实验得到 HTTP 200。 |
| `docker logs --tail 5 lab1-nginx` | 查看容器日志的最后 5 行。-f 持续跟踪，-t 显示时间戳。原实验看到了对应的 HEAD 请求。 |
| `docker exec lab1-nginx ps aux` | 在运行中的容器内查看进程。原实验里 Nginx 主进程的 PID 是 1。 |
| `docker inspect lab1-nginx --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"` | 用 --format 从网络配置里取容器 IP。原实验得到 172.17.0.3，实际地址可能变化。 |

#### 验证文件改动的归属

```cmd
docker exec lab1-nginx sh -c "echo '<h1>Lab1: edited INSIDE the container</h1>' > /usr/share/nginx/html/index.html"
docker diff lab1-nginx
docker stop lab1-nginx
docker start lab1-nginx
curl.exe -s http://localhost:8081
```

sh -c 执行引号内的命令，> 在容器内覆盖首页。docker diff 中 A、C、D 分别表示新增、修改、删除。-s 隐藏下载进度。原实验在停止并启动同一个容器后仍看到修改过的首页。

原笔记另用临时容器 lab1-tmp 做了对照。用 docker rm -f lab1-tmp 删除运行中的临时容器，再用原镜像和 8082:80 重建，访问时看到镜像自带的欢迎页。另一次实测在容器内删除站点目录后得到 404，重启同一容器仍是 404，用原镜像重建后恢复为 200。需要长期保存的文件可通过实验 02 的挂载保存。

### 本次遇到的报错

| 现象 | 原因和处理 |
| --- | --- |
| 容器显示 Up，但 curl 报 Empty reply from server | 实验把 8083 映射到了容器的 81，Nginx 实际监听 80。核对 -p 的右侧，用 HTTP 请求验证。 |
| Windows 找不到 lab1-nginx | 在 cmd 输入了 start lab1-nginx，调用的是 Windows 的 start。改用 docker start lab1-nginx。 |
| port is already allocated | 8081 已被占用。用 docker ps 查看现有映射，或用 netstat -ano 查看本机监听。创建失败的实验容器可能留在 Created 状态，可用 docker ps -a 确认。 |
| docker rmi nginx:alpine 报镜像被容器引用 | 原实验中有容器引用此镜像。要删除镜像时，先确认引用它的容器可以删除，再用 docker rm 和 docker rmi。 |
| inspect 模板报找不到 IPAddress 字段 | 用上表中的模板从 .NetworkSettings.Networks 读取网络地址。 |

### 自测回顾

1. docker images 和 docker ps -a 分别查看什么？前者查看镜像，后者查看容器。
2. -p 8081:80 中哪个端口必须与 Nginx 监听端口一致？右边的 80。
3. 为什么 hello-world 加 -d 也会显示 Exited (0)？主进程执行完就正常退出了。
4. 修改首页后，停止再启动与删除再重建有何区别？前者沿用可写层，后者从镜像创建新的可写层。


---

## 实验 02｜数据卷 Volume

### 任务与知识点

把 Nginx 首页放到容器可写层之外，验证删除并重建容器后文件仍可读取。

| 方式 | -v 写法 | 数据在哪里 |
| --- | --- | --- |
| 绑定挂载 | `-v D:\data:/path` | 指定的宿主机目录或文件 |
| 命名卷 | `-v lab2data:/path` | Docker 管理的存储，通过卷名引用 |
| 匿名卷 | `-v /path` | Docker 管理的存储，自动生成名称 |

-v 的左边是挂载源，右边是容器内路径。挂载后，容器在该路径看到的是挂载源的内容。默认情况下，空数据卷挂到镜像中已有文件的目录时，Docker 会先把这些文件复制进卷。绑定挂载会直接显示宿主机文件或目录。加 :ro 可限制容器写入挂载点。

### 实验操作

在 Windows 命令提示符中逐条执行。以下结果是复做实验时的预期。

#### 1. 绑定挂载宿主机目录

```cmd
mkdir D:\myskills\dockerskill\lab2-data
docker run -d --name lab2-bind -p 8093:80 -v D:\myskills\dockerskill\lab2-data:/usr/share/nginx/html nginx:alpine
curl.exe -I http://localhost:8093
```

新建的目录为空时，预期返回 403。镜像里的首页被挂载遮住，Nginx 也不允许列出目录。若该目录已经有 index.html，则可直接读到已有文件。

```cmd
echo hello from my Windows folder > D:\myskills\dockerskill\lab2-data\index.html
curl.exe -s http://localhost:8093
docker exec lab2-bind sh -c "echo 'edited INSIDE container' > /usr/share/nginx/html/index.html"
type D:\myskills\dockerskill\lab2-data\index.html
```

curl.exe -s 显示网页正文并隐藏进度。type 显示宿主机文件内容，预期为 edited INSIDE container，验证容器写入的是同一份文件。用 docker rm -f lab2-bind 删除演示容器，再用同一条 docker run 重建，仍可读到该文件。做完可删除演示容器，保留目录供只读实验使用。

#### 2. 命名卷与容器重建

```cmd
docker volume create lab2data
docker volume ls
docker volume inspect lab2data
docker run -d --name lab2-vol -p 8094:80 -v lab2data:/usr/share/nginx/html nginx:alpine
curl.exe -I http://localhost:8094
docker exec lab2-vol ls /usr/share/nginx/html
```

volume create 创建命名卷，ls 列出卷，inspect 查看详细信息。Mountpoint 是 Docker 引擎所在 Linux 环境里的路径。在 Docker Desktop 中可通过挂载卷的容器读取数据。新建空卷预期得到 HTTP 200，并能列出 index.html 和 50x.html。

```cmd
docker exec lab2-vol sh -c "echo 'volume data survives' > /usr/share/nginx/html/index.html"
docker rm -f lab2-vol
docker run -d --name lab2-vol2 -p 8094:80 -v lab2data:/usr/share/nginx/html nginx:alpine
curl.exe -s http://localhost:8094
```

-f 允许删除运行中的演示容器。新容器挂载同一个卷，预期仍返回 volume data survives。有容器引用时，docker volume rm lab2data 会报 volume is in use。完成验证后，如果实验数据可以丢弃，先移除 lab2-vol2，再删除 lab2data。

#### 3. 匿名卷与只读挂载

```cmd
docker run -d --name lab2-anon -p 8095:80 -v /usr/share/nginx/html nginx:alpine
docker volume ls
docker run -d --name lab2-ro -p 8096:80 -v D:\myskills\dockerskill\lab2-data:/usr/share/nginx/html:ro nginx:alpine
curl.exe -s http://localhost:8096
docker exec lab2-ro sh -c "echo x > /usr/share/nginx/html/index.html"
```

-v 只给目标路径时，卷列表会出现 Docker 自动生成的卷名。只读挂载预期可以读到原首页，写入时报 Read-only file system。收尾时可用 docker rm -fv lab2-anon 删除该演示容器及其匿名卷，再用 docker rm -f lab2-ro 删除只读演示容器。

### 常见报错

| 报错 | 原因和处理 |
| --- | --- |
| 403 Forbidden | 绑定挂载的目录为空。向宿主机目录写入 index.html 后再访问。 |
| volume is in use | 仍有容器引用这个卷，已停止的容器也算。确认相关容器可删除后，再删卷。 |
| invalid reference format 或挂载路径解析失败 | 在本实验的 Windows cmd 中使用带盘符的绝对路径。路径含空格时，将整个 -v 参数值加引号。 |
| Read-only file system | :ro 生效。容器需要写数据时，使用可写挂载路径。 |

### 自测回顾

1. 为什么空目录绑定挂载返回 403，而空卷返回 200？前者遮住了镜像首页，后者默认先将首页复制进空卷。
2. 为什么重建容器后还能读到改过的网页？新容器挂载了同一个宿主机目录或命名卷。
3. MySQL 数据目录适合用什么挂载？在本地 Docker Desktop 实验里可用命名卷，便于管理，也减少 Windows 路径和权限差异。
4. 如何把配置文件挂进去并限制容器写入？确认源文件存在，再在绑定挂载的参数末尾加 :ro。


---

## 实验 03｜用 Dockerfile 构建自定义镜像

### 任务目标

将自定义首页打包进 Nginx 镜像。删除旧容器后用同一个镜像创建新容器，确认新容器仍能提供这份首页。

### 知识点

| 指令 | 何时使用 | 本实验的作用 |
| --- | --- | --- |
| `FROM` | 构建时 | 选择已安装 Nginx 的基础镜像 |
| `RUN` | 构建时 | 把首页写进镜像的文件系统层 |
| `CMD` | 容器启动时 | 提供默认启动命令，让 Nginx 保持在前台 |

Dockerfile 是构建配方。修改并保存它后，需要再次执行 `docker build` 才能将改动打进镜像。容器有自己的可写层，通过 `docker exec` 修改容器内的普通文件时，镜像里的文件保持原样。

Lab 02 的数据卷用于保存数据库记录等运行时数据。Lab 03 的镜像用于打包随应用发布的文件，例如站点首页。

### 实验操作

在 Windows 命令提示符中，用 `mkdir lab03-dockerfile` 创建实验目录，再用 `cd lab03-dockerfile` 进入目录。创建名为 `Dockerfile` 的纯文本文件，内容如下。

```dockerfile
FROM nginx:alpine
RUN echo '<h1>Hello from Lab 03</h1>' > /usr/share/nginx/html/index.html
CMD ["nginx", "-g", "daemon off;"]
```

`alpine` 是基础镜像的标签。`>` 将输出写入并覆盖默认首页。`-g` 向 Nginx 传入全局配置，`daemon off;` 让它在前台运行。

在 Dockerfile 所在目录逐条执行下表中的命令。

| 命令 | 参数与预期结果 |
| --- | --- |
| `docker build -t lab03-nginx:v1 .` | `-t` 指定镜像名和标签，末尾的 `.` 将当前目录作为构建上下文。 |
| `docker image ls lab03-nginx` | 按镜像名查看本地镜像，预期看到标签 `v1`。 |
| `docker run -d --name lab03-web -p 127.0.0.1:8083:80 lab03-nginx:v1` | `-d` 在后台运行，`--name` 指定容器名，`-p` 将本机回环地址的 `8083` 端口映射到容器的 `80` 端口。最后一个参数指定镜像。 |
| `docker stop lab03-web` | 用容器名指定要停止的容器。 |
| `docker rm lab03-web` | 用容器名指定要删除的已停止容器。 |

启动后访问 [本地实验网页](http://127.0.0.1:8083)，应看到 **Hello from Lab 03**。停止并删除容器后，再执行同一条 `docker run` 命令。按 `Ctrl + F5` 刷新网页，应再次看到同样的首页。

### 本次遇到的报错

| 报错 | 原因和处理 |
| --- | --- |
| `unknown shorthand flag: 't'` | 把 `build` 写成了 `built`。改回 `docker build`。 |
| `requires 1 argument` | 构建和查看镜像的命令粘在了同一行。构建命令到 `.` 结束，等它跑完再单独执行查看命令。 |
| `open Dockerfile: no such file or directory` | 实际文件名是 `Dockerfile.txt`。在命令提示符中执行 `dir /a /b` 查看完整文件名，再用 `ren Dockerfile.txt Dockerfile` 改名。 |

### 自测

1. 只修改 Dockerfile，现有的 `v1` 镜像会自动更新吗？
2. 如果本机 `8083` 已被占用，端口映射里该改哪个数字？
3. 如果用 `docker exec` 修改当前容器的首页，再用同一个镜像创建新容器，新容器会显示哪一版？

参考答案分别是：需要重新构建镜像、改本机端口 `8083`、显示镜像里原本的首页。


---

## 实验 04｜用 Docker Compose 管理多个容器

### 任务与知识点

用一份 `compose.yaml` 启动 Nginx 和 MySQL。写入一条 MySQL 记录，删除并重建容器，再查询同一条记录，验证命名卷的数据持久化。

- Dockerfile 定义镜像如何构建。Compose 文件定义服务如何运行。
- Compose 从 `services` 读取服务，从各服务的 `image` 读取镜像。本地缺少实验镜像时，会从 Docker Hub 下载对应镜像。
- `mysql-data:/var/lib/mysql` 左边是命名卷，右边是 MySQL 容器内的数据目录。
- 容器显示 `Up` 表示它正在运行。实际登录并执行 `SELECT 1` 才能验证 MySQL 可以接收连接和执行查询。

### 实验配置

在 Windows 命令提示符中，用 `docker compose version` 查看 Compose 版本。在 `D:\myskills\dockerskill\lab04-compose` 中创建 `compose.yaml`，留意 YAML 缩进和实际文件扩展名。

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "127.0.0.1:8084:80"
  db:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: "lab04-local-password"
    volumes:
      - mysql-data:/var/lib/mysql

volumes:
  mysql-data:
```

`127.0.0.1:8084:80` 把本机回环地址的 `8084` 映射到 Nginx 容器的 `80`。MySQL 的 root 密码用于首次初始化，示例密码仅用于本地实验。底部的 `volumes` 声明命名卷。

### 启动与验证

在 `compose.yaml` 所在目录逐步执行。

| 命令 | 作用与预期结果 |
| --- | --- |
| `docker compose config --quiet` | 检查配置，`--quiet` 省略展开后的配置。检查通过时通常没有输出。 |
| `docker compose up -d` | 创建并启动服务及所需资源，`-d` 让服务在后台运行。 |
| `docker compose ps -a` | 查看项目的容器，`-a` 包含已退出的容器。预期两个服务均显示 `Up`。 |
| `docker compose exec db mysql -u root -p -e "SELECT 1;"` | 在 `db` 容器运行 MySQL 客户端。用 `-u root` 指定用户，`-p` 提示输入密码，`-e` 执行引号内的 SQL。预期返回 `1`。 |

每次看到 `Enter password:` 时输入配置里的密码。输入时终端不会显示字符。Nginx 可通过本机的 `http://127.0.0.1:8084` 访问。

### 验证容器重建后数据仍在

1. 创建实验库和表，写入并查询一条记录。重复执行时会跳过已有的库、表和相同主键的记录。

   ```cmd
   docker compose exec db mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS lab04; CREATE TABLE IF NOT EXISTS lab04.notes (id INT PRIMARY KEY, message VARCHAR(100)); INSERT IGNORE INTO lab04.notes VALUES (1, 'Hello from Lab 04'); SELECT * FROM lab04.notes;"
   ```

2. 执行 `docker compose down`，停止并删除服务容器和项目默认网络。默认保留命名卷。本实验使用不带 `-v` 的命令，因为 `-v` 会移除项目声明的命名卷。
3. 执行 `docker compose up -d`，创建新容器。Compose 会把已有的命名卷重新挂载到新 MySQL 容器。
4. 只读查询原来的记录。

   ```cmd
   docker compose exec db mysql -u root -p -e "SELECT id, message FROM lab04.notes WHERE id = 1;"
   ```

   预期返回 `1 | Hello from Lab 04`。查询到这一行即验证了数据在容器重建后仍存在。

### 自测回顾

- **Compose 从哪里知道启动什么？** 服务名、镜像、端口映射和卷挂载都由 `compose.yaml` 指定。
- **记录保存在哪里？** 保存在 `mysql-data` 命名卷里，MySQL 通过容器内的 `/var/lib/mysql` 读写。
- **为什么用 `down` 做验证？** `stop` 只停止原容器，`down` 会移除它。从新容器查询到旧记录，就能验证卷的数据持久化。


---

## 实验 05｜自定义 Docker 网络

### 目标与知识点

创建自定义桥接网络，让测试容器通过容器名访问 Nginx。Docker 会在该网络内将容器名解析为对应的容器 IP。HTTP 默认访问目标容器的 80 端口。若要让宿主机通过映射端口访问，再配置 `-p`。

Lab 04 中，Compose 自动创建项目网络，服务可以用服务名互访。本实验手动创建网络，并在创建容器时用 `--network` 指定它。

### 实验操作

```cmd
docker network create --driver bridge lab05-net
docker run -d --name lab05-web --network lab05-net nginx:alpine
docker run --rm --network lab05-net busybox:1.37 wget -qO - http://lab05-web
```

在 Windows 命令窗口逐条执行。

1. `--driver bridge` 指定桥接网络，`lab05-net` 是网络名。成功时输出网络 ID。已有容器需要显式接入。
2. `-d` 让 Nginx 在后台运行，`--name lab05-web` 指定容器名，`--network lab05-net` 让它加入实验网络。成功时输出容器 ID。
3. 测试容器也加入 `lab05-net`。`--rm` 让测试容器退出后自动删除。`wget` 的 `-q` 隐藏下载进度，`-O -` 把响应正文输出到终端。看到包含 `Welcome to nginx!` 的 HTML，即验证了容器名称解析和 HTTP 访问。

### wget 命令拆解

`wget` 是命令行下载工具，可以通过网址获取网页或文件。本实验中，它在 BusyBox 容器里运行，向 Nginx 请求首页。

```sh
wget -q -O - http://lab05-web
```

- `-q` 启用静默模式，隐藏下载进度等信息。
- `-O -` 指定输出位置。这里是大写字母 `O`，后面的 `-` 表示把收到的网页源码打印到终端。
- `http://lab05-web` 是请求地址，`lab05-web` 是 Nginx 容器名。

实验命令里的 `-qO -` 是 `-q -O -` 的合写形式。终端中的 `Welcome to nginx!` 来自 Nginx 返回的 HTML。

### 本次排错

- `network la05-net not found` 表示创建容器时指定的网络名少了一个 `b`。容器停留在 `Created` 状态，重试 `docker start lab05-web` 会沿用原来的网络配置。
- 再次执行 `docker run` 遇到名称冲突时，用 `docker ps -a --filter "name=lab05-web"` 查找已有容器。`-a` 包含未运行的容器，`--filter` 按名称筛选。
- 用 `docker network ls --filter "name=lab05-net"` 检查正确的网络是否存在。确认原容器是本实验中启动失败的容器后，用 `docker rm lab05-web` 删除它，再用正确的 `--network lab05-net` 重新创建。

### 自测回顾

**为什么没有用 `-p`，测试容器依然能访问 Nginx？**

两个容器加入同一个自定义桥接网络，Docker 可以把 `lab05-web` 解析成目标容器的 IP。测试容器直接连接 Nginx 监听的 80 端口，HTTP URL 省略端口时默认使用 80。


---

## 实验 06｜综合实践：部署留言板

### 总体梳理

#### 1. 请求怎么走

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

#### 2. 服务怎么启动

`docker compose up -d --build` 根据 `compose.yaml` 组装三个服务。Dockerfile 把 `app.py` 和 `requirements.txt` 中的依赖打包进应用镜像。构建时由 `RUN` 安装依赖，容器启动时由 `CMD` 运行 Gunicorn。MySQL 通过健康检查后，Compose 才启动依赖它的应用。Nginx 使用现成镜像，并挂载 `nginx.conf` 来转发请求。

#### 3. 数据存在哪里

MySQL 将数据写入挂载了 `mysql-data` 的 `/var/lib/mysql`。执行 `docker compose down` 后，命名卷会保留。再次执行 `docker compose up -d` 时，新 MySQL 容器挂载原卷，所以应用能查到旧留言。若用 `docker compose down -v`，这个卷会随项目一起删除，下次启动将初始化空库。

#### 排错对照与复习

- 临时应用容器使用 `DB_HOST=localhost` 时，会尝试连接自身的 MySQL 端口，预期连接失败并返回 `HTTP 500`。使用 `DB_HOST=db` 时，Compose 网络把服务名解析到 MySQL 容器，预期返回 `HTTP 200`。Flask 测试客户端直接请求应用，测试范围是应用与数据库的连接。
- **复习题**　如果浏览器入口改成 `8090`，只需将 Compose 端口映射改为 `127.0.0.1:8090:80`。为什么 `app:8000`、`db:3306` 和 `mysql-data` 可以沿用？因为这次修改的是 Windows 入口，容器间的地址和卷挂载仍然有效。

### 任务与知识点

用 Dockerfile 打包 Flask 应用，用 Compose 编排 Nginx、Gunicorn/Flask 和 MySQL。提交留言后重建容器，验证数据保留。再用临时容器对照测试错误与正确的数据库地址。

| 链路 | 地址 | 用途 |
| --- | --- | --- |
| Windows 浏览器 → Nginx | 127.0.0.1:8086 → web:80 | Compose 发布 Nginx 的端口 |
| Nginx → 应用 | app:8000 | Nginx 通过 Compose 服务名转发请求 |
| 应用 → MySQL | db:3306 | PyMySQL 通过服务名连接数据库 |

容器中的 localhost 指向该容器自身。应用和数据库在同一个 Compose 网络里通信，无需向 Windows 发布各自的端口。

### 实验配置

实验目录为 D:\myskills\dockerskill\lab06-message-board。Windows 命令提示符中可用 cd /d 切换目录和盘符。

| 文件 | 内容 |
| --- | --- |
| app.py | Flask 处理 GET 和 POST。GET 用 SELECT 读取留言，POST 用参数化 INSERT 写入并提交。 |
| requirements.txt | Flask、PyMySQL[rsa] 和 gunicorn。PyMySQL 是数据库驱动，[rsa] 提供认证所需的额外依赖。 |
| Dockerfile | 基于 python:3.12-slim。RUN pip install 在构建时安装依赖，CMD 在容器启动时执行 Gunicorn 并监听 0.0.0.0:8000。先复制依赖清单再复制代码，便于复用安装层缓存。 |
| nginx.conf | 监听 80，用 proxy_pass http://app:8000 转发请求。Compose 通过只读绑定挂载将配置放到 /etc/nginx/conf.d/default.conf。 |
| compose.yaml | web 发布 8086，app 使用 build: . 构建镜像，db 使用 mysql:8.4 并把 mysql-data 挂到 /var/lib/mysql。 |

应用的 DB_NAME、DB_USER 和 DB_PASSWORD 要与 MySQL 初始化配置对应。DB_HOST 填 db。MySQL 健康检查通过 TCP 使用应用账户执行 SELECT 1。Compose 等 db 健康后再启动 app。健康检查中的双美元符号让环境变量在容器中展开。

### 启动与持久化验证

| 命令或操作 | 作用与预期结果 |
| --- | --- |
| `docker compose config --quiet` | 检查 Compose 配置。--quiet 省略展开后的配置。 |
| `docker compose up -d --build` | 构建应用镜像并启动服务。-d 在后台运行，--build 在启动前构建镜像。 |
| 打开 http://127.0.0.1:8086/ | 预期显示留言板。提交一条测试留言后，应出现在列表中。 |
| `docker compose down` | 停止并删除服务容器及默认网络，保留命名卷。 |
| `docker compose up -d` | 使用原配置重建容器，重新挂载已有的 mysql-data。 |
| 刷新留言板 | 原留言仍然显示时，即验证了数据持久化。 |

down 加 -v 会删除本项目声明的命名卷，下次启动会初始化空数据库。

### 排错练习

构建时曾在 FROM python:3.12-slim 处收到 EOF。日志显示 Docker 请求镜像站的镜像信息时连接提前结束。用 docker pull python:3.12-slim 单独检查基础镜像能否拉取，拉取成功后再重试构建。

下面两条命令分别测试错误和正确的数据库地址。run 创建临时应用容器，--rm 让它退出后自动删除，--no-deps 跳过启动依赖，-e 只覆盖这次运行的环境变量。python -c 运行引号中的代码，用 Flask 测试客户端请求首页。

```cmd
docker compose run --rm --no-deps -e DB_HOST=localhost app python -c "from app import app; print('HTTP', app.test_client().get('/').status_code)"
docker compose run --rm --no-deps app python -c "from app import app; print('HTTP', app.test_client().get('/').status_code)"
```

第一条预期在日志中看到连接 localhost 失败并返回 HTTP 500。第二条沿用 DB_HOST=db，预期返回 HTTP 200。这两条命令不修改 Compose 文件或正在运行的服务。

### 自测回顾

1. pip install 什么时候执行？Dockerfile 的 RUN 在构建阶段执行，Gunicorn 由 CMD 在容器启动时启动。
2. 浏览器访问 8086 后，Nginx 转发到哪里？Docker 先把流量映射到 Nginx 的 80，再由 Nginx 转发到 app:8000。
3. 留言写在哪里？MySQL 通过 /var/lib/mysql 写入 mysql-data 命名卷。
4. 应用的数据库地址为什么是 db？Compose 网络用服务名定位容器，localhost 会连接应用容器自身。
