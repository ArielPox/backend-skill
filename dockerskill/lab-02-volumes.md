# 实验 02｜数据卷 Volume

## 任务与知识点

把 Nginx 首页放到容器可写层之外，验证删除并重建容器后文件仍可读取。

| 方式 | -v 写法 | 数据在哪里 |
| --- | --- | --- |
| 绑定挂载 | `-v D:\data:/path` | 指定的宿主机目录或文件 |
| 命名卷 | `-v lab2data:/path` | Docker 管理的存储，通过卷名引用 |
| 匿名卷 | `-v /path` | Docker 管理的存储，自动生成名称 |

-v 的左边是挂载源，右边是容器内路径。挂载后，容器在该路径看到的是挂载源的内容。默认情况下，空数据卷挂到镜像中已有文件的目录时，Docker 会先把这些文件复制进卷。绑定挂载会直接显示宿主机文件或目录。加 :ro 可限制容器写入挂载点。

## 实验操作

在 Windows 命令提示符中逐条执行。以下结果是复做实验时的预期。

### 1. 绑定挂载宿主机目录

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

### 2. 命名卷与容器重建

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

### 3. 匿名卷与只读挂载

```cmd
docker run -d --name lab2-anon -p 8095:80 -v /usr/share/nginx/html nginx:alpine
docker volume ls
docker run -d --name lab2-ro -p 8096:80 -v D:\myskills\dockerskill\lab2-data:/usr/share/nginx/html:ro nginx:alpine
curl.exe -s http://localhost:8096
docker exec lab2-ro sh -c "echo x > /usr/share/nginx/html/index.html"
```

-v 只给目标路径时，卷列表会出现 Docker 自动生成的卷名。只读挂载预期可以读到原首页，写入时报 Read-only file system。收尾时可用 docker rm -fv lab2-anon 删除该演示容器及其匿名卷，再用 docker rm -f lab2-ro 删除只读演示容器。

## 常见报错

| 报错 | 原因和处理 |
| --- | --- |
| 403 Forbidden | 绑定挂载的目录为空。向宿主机目录写入 index.html 后再访问。 |
| volume is in use | 仍有容器引用这个卷，已停止的容器也算。确认相关容器可删除后，再删卷。 |
| invalid reference format 或挂载路径解析失败 | 在本实验的 Windows cmd 中使用带盘符的绝对路径。路径含空格时，将整个 -v 参数值加引号。 |
| Read-only file system | :ro 生效。容器需要写数据时，使用可写挂载路径。 |

## 自测回顾

1. 为什么空目录绑定挂载返回 403，而空卷返回 200？前者遮住了镜像首页，后者默认先将首页复制进空卷。
2. 为什么重建容器后还能读到改过的网页？新容器挂载了同一个宿主机目录或命名卷。
3. MySQL 数据目录适合用什么挂载？在本地 Docker Desktop 实验里可用命名卷，便于管理，也减少 Windows 路径和权限差异。
4. 如何把配置文件挂进去并限制容器写入？确认源文件存在，再在绑定挂载的参数末尾加 :ro。
