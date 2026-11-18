# 实操复习｜设备分页与 HTTP 状态码

在 Windows CMD 中操作。课程目录为 `D:\myskills\SQLAIchemy-AIembic-skill`。保持 Uvicorn 监听 `127.0.0.1:8000`。沿用设备导入实操创建的项目，其中有两台设备。下方命令里的 `PROJECT_ID` 需换成查库得到的数字项目 ID。

## 1. 验证第二页

```cmd
curl.exe -i "http://127.0.0.1:8000/api/v1/projects/PROJECT_ID/devices?page=2&page_size=1"
```

预期 HTTP 200、`total=2` 和一条设备。截图确认正文中 `total=2`，且 `items` 有一条设备。

## 2. 验证超出最后一页

```cmd
curl.exe -i "http://127.0.0.1:8000/api/v1/projects/PROJECT_ID/devices?page=3&page_size=1"
```

预期 HTTP 200 和 `{"total":2,"items":[]}`。总数统计分页前的匹配记录。

截图确认首次请求将 `PROJECT_ID` 原样发出，返回 HTTP 422，错误位置为 `path.project_id`，类型为 `int_parsing`。修复时从 CMD 历史调出成功的第二页命令，保留数字项目 ID，仅修改页码。修复后学习者回复「1」，原始响应未贴出。

## 3. 验证项目不存在

```cmd
curl.exe -i "http://127.0.0.1:8000/api/v1/projects/-1/devices?page=1&page_size=1"
```

本实验用 `-1` 表示查不到的项目，预期 HTTP 404。学习者回复「1」，原始状态行未贴出。

## 自测与讲评

1. 项目有两台设备，每页一台。把页码从 2 改成 3，HTTP 状态、`total` 和 `items` 分别是什么？

   **参考答案**　返回 `200 OK`，`total=2`，`items=[]`。总数统计分页前的匹配记录，第三页没有可返回的设备。

2. 为什么字面量 `PROJECT_ID` 返回 422，而本实验的 `-1` 返回 404？

   **参考答案**　`PROJECT_ID` 无法通过整数路径参数校验。`-1` 能通过整数校验，接口查库后发现项目不存在。
