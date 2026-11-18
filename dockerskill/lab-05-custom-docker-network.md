# 实验 05｜自定义 Docker 网络

## 目标与知识点

创建自定义桥接网络，让测试容器通过容器名访问 Nginx。Docker 会在该网络内将容器名解析为对应的容器 IP。HTTP 默认访问目标容器的 80 端口。若要让宿主机通过映射端口访问，再配置 `-p`。

Lab 04 中，Compose 自动创建项目网络，服务可以用服务名互访。本实验手动创建网络，并在创建容器时用 `--network` 指定它。

## 实验操作

```cmd
docker network create --driver bridge lab05-net
docker run -d --name lab05-web --network lab05-net nginx:alpine
docker run --rm --network lab05-net busybox:1.37 wget -qO - http://lab05-web
```

在 Windows 命令窗口逐条执行。

1. `--driver bridge` 指定桥接网络，`lab05-net` 是网络名。成功时输出网络 ID。已有容器需要显式接入。
2. `-d` 让 Nginx 在后台运行，`--name lab05-web` 指定容器名，`--network lab05-net` 让它加入实验网络。成功时输出容器 ID。
3. 测试容器也加入 `lab05-net`。`--rm` 让测试容器退出后自动删除。`wget` 的 `-q` 隐藏下载进度，`-O -` 把响应正文输出到终端。看到包含 `Welcome to nginx!` 的 HTML，即验证了容器名称解析和 HTTP 访问。

## wget 命令拆解

`wget` 是命令行下载工具，可以通过网址获取网页或文件。本实验中，它在 BusyBox 容器里运行，向 Nginx 请求首页。

```sh
wget -q -O - http://lab05-web
```

- `-q` 启用静默模式，隐藏下载进度等信息。
- `-O -` 指定输出位置。这里是大写字母 `O`，后面的 `-` 表示把收到的网页源码打印到终端。
- `http://lab05-web` 是请求地址，`lab05-web` 是 Nginx 容器名。

实验命令里的 `-qO -` 是 `-q -O -` 的合写形式。终端中的 `Welcome to nginx!` 来自 Nginx 返回的 HTML。

## 本次排错

- `network la05-net not found` 表示创建容器时指定的网络名少了一个 `b`。容器停留在 `Created` 状态，重试 `docker start lab05-web` 会沿用原来的网络配置。
- 再次执行 `docker run` 遇到名称冲突时，用 `docker ps -a --filter "name=lab05-web"` 查找已有容器。`-a` 包含未运行的容器，`--filter` 按名称筛选。
- 用 `docker network ls --filter "name=lab05-net"` 检查正确的网络是否存在。确认原容器是本实验中启动失败的容器后，用 `docker rm lab05-web` 删除它，再用正确的 `--network lab05-net` 重新创建。

## 自测回顾

**为什么没有用 `-p`，测试容器依然能访问 Nginx？**

两个容器加入同一个自定义桥接网络，Docker 可以把 `lab05-web` 解析成目标容器的 IP。测试容器直接连接 Nginx 监听的 80 端口，HTTP URL 省略端口时默认使用 80。
