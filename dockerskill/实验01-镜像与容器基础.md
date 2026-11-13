# 实验 01｜镜像与容器基础

## 任务目标

在 Windows 10 的 Docker Desktop（WSL2 后端）中运行 Nginx，从本机访问网页，并验证停止、重启和删除容器对文件改动的影响。

## 知识点

- **镜像**是由只读层组成的运行模板。标签可以表示版本或变体，例如 nginx:alpine。省略标签时默认用 latest，标签所指的镜像可以更新。
- **容器**由镜像创建。主进程退出时容器停止。-d 让 Docker 客户端在启动后返回终端，容器的运行时间取决于主进程。
- **端口映射**按“宿主机端口:容器端口”填写。8081:80 把访问本机 8081 的请求转到 Nginx 监听的 80。只供本机访问时，可写成 127.0.0.1:8081:80。
- **容器可写层**记录容器内普通文件的新增、修改和删除。stop/start 保留这层，rm 删除容器时会移除这层。同一镜像创建的新容器有自己的可写层。

## 实验操作

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

### 验证文件改动的归属

```cmd
docker exec lab1-nginx sh -c "echo '<h1>Lab1: edited INSIDE the container</h1>' > /usr/share/nginx/html/index.html"
docker diff lab1-nginx
docker stop lab1-nginx
docker start lab1-nginx
curl.exe -s http://localhost:8081
```

sh -c 执行引号内的命令，> 在容器内覆盖首页。docker diff 中 A、C、D 分别表示新增、修改、删除。-s 隐藏下载进度。原实验在停止并启动同一个容器后仍看到修改过的首页。

原笔记另用临时容器 lab1-tmp 做了对照。用 docker rm -f lab1-tmp 删除运行中的临时容器，再用原镜像和 8082:80 重建，访问时看到镜像自带的欢迎页。另一次实测在容器内删除站点目录后得到 404，重启同一容器仍是 404，用原镜像重建后恢复为 200。需要长期保存的文件可通过实验 02 的挂载保存。

## 本次遇到的报错

| 现象 | 原因和处理 |
| --- | --- |
| 容器显示 Up，但 curl 报 Empty reply from server | 实验把 8083 映射到了容器的 81，Nginx 实际监听 80。核对 -p 的右侧，用 HTTP 请求验证。 |
| Windows 找不到 lab1-nginx | 在 cmd 输入了 start lab1-nginx，调用的是 Windows 的 start。改用 docker start lab1-nginx。 |
| port is already allocated | 8081 已被占用。用 docker ps 查看现有映射，或用 netstat -ano 查看本机监听。创建失败的实验容器可能留在 Created 状态，可用 docker ps -a 确认。 |
| docker rmi nginx:alpine 报镜像被容器引用 | 原实验中有容器引用此镜像。要删除镜像时，先确认引用它的容器可以删除，再用 docker rm 和 docker rmi。 |
| inspect 模板报找不到 IPAddress 字段 | 用上表中的模板从 .NetworkSettings.Networks 读取网络地址。 |

## 自测回顾

1. docker images 和 docker ps -a 分别查看什么？前者查看镜像，后者查看容器。
2. -p 8081:80 中哪个端口必须与 Nginx 监听端口一致？右边的 80。
3. 为什么 hello-world 加 -d 也会显示 Exited (0)？主进程执行完就正常退出了。
4. 修改首页后，停止再启动与删除再重建有何区别？前者沿用可写层，后者从镜像创建新的可写层。
