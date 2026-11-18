# 实验 04｜用 Docker Compose 管理多个容器

## 任务与知识点

用一份 `compose.yaml` 启动 Nginx 和 MySQL。写入一条 MySQL 记录，删除并重建容器，再查询同一条记录，验证命名卷的数据持久化。

- Dockerfile 定义镜像如何构建。Compose 文件定义服务如何运行。
- Compose 从 `services` 读取服务，从各服务的 `image` 读取镜像。本地缺少实验镜像时，会从 Docker Hub 下载对应镜像。
- `mysql-data:/var/lib/mysql` 左边是命名卷，右边是 MySQL 容器内的数据目录。
- 容器显示 `Up` 表示它正在运行。实际登录并执行 `SELECT 1` 才能验证 MySQL 可以接收连接和执行查询。

## 实验配置

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

## 启动与验证

在 `compose.yaml` 所在目录逐步执行。

| 命令 | 作用与预期结果 |
| --- | --- |
| `docker compose config --quiet` | 检查配置，`--quiet` 省略展开后的配置。检查通过时通常没有输出。 |
| `docker compose up -d` | 创建并启动服务及所需资源，`-d` 让服务在后台运行。 |
| `docker compose ps -a` | 查看项目的容器，`-a` 包含已退出的容器。预期两个服务均显示 `Up`。 |
| `docker compose exec db mysql -u root -p -e "SELECT 1;"` | 在 `db` 容器运行 MySQL 客户端。用 `-u root` 指定用户，`-p` 提示输入密码，`-e` 执行引号内的 SQL。预期返回 `1`。 |

每次看到 `Enter password:` 时输入配置里的密码。输入时终端不会显示字符。Nginx 可通过本机的 `http://127.0.0.1:8084` 访问。

## 验证容器重建后数据仍在

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

## 自测回顾

- **Compose 从哪里知道启动什么？** 服务名、镜像、端口映射和卷挂载都由 `compose.yaml` 指定。
- **记录保存在哪里？** 保存在 `mysql-data` 命名卷里，MySQL 通过容器内的 `/var/lib/mysql` 读写。
- **为什么用 `down` 做验证？** `stop` 只停止原容器，`down` 会移除它。从新容器查询到旧记录，就能验证卷的数据持久化。
