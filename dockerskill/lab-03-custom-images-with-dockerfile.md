# 实验 03｜用 Dockerfile 构建自定义镜像

## 任务目标

将自定义首页打包进 Nginx 镜像。删除旧容器后用同一个镜像创建新容器，确认新容器仍能提供这份首页。

## 知识点

| 指令 | 何时使用 | 本实验的作用 |
| --- | --- | --- |
| `FROM` | 构建时 | 选择已安装 Nginx 的基础镜像 |
| `RUN` | 构建时 | 把首页写进镜像的文件系统层 |
| `CMD` | 容器启动时 | 提供默认启动命令，让 Nginx 保持在前台 |

Dockerfile 是构建配方。修改并保存它后，需要再次执行 `docker build` 才能将改动打进镜像。容器有自己的可写层，通过 `docker exec` 修改容器内的普通文件时，镜像里的文件保持原样。

Lab 02 的数据卷用于保存数据库记录等运行时数据。Lab 03 的镜像用于打包随应用发布的文件，例如站点首页。

## 实验操作

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

## 本次遇到的报错

| 报错 | 原因和处理 |
| --- | --- |
| `unknown shorthand flag: 't'` | 把 `build` 写成了 `built`。改回 `docker build`。 |
| `requires 1 argument` | 构建和查看镜像的命令粘在了同一行。构建命令到 `.` 结束，等它跑完再单独执行查看命令。 |
| `open Dockerfile: no such file or directory` | 实际文件名是 `Dockerfile.txt`。在命令提示符中执行 `dir /a /b` 查看完整文件名，再用 `ren Dockerfile.txt Dockerfile` 改名。 |

## 自测

1. 只修改 Dockerfile，现有的 `v1` 镜像会自动更新吗？
2. 如果本机 `8083` 已被占用，端口映射里该改哪个数字？
3. 如果用 `docker exec` 修改当前容器的首页，再用同一个镜像创建新容器，新容器会显示哪一版？

参考答案分别是：需要重新构建镜像、改本机端口 `8083`、显示镜像里原本的首页。
