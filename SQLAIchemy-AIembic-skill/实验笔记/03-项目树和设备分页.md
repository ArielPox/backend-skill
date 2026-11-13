# 实验 03｜项目树和设备分页

## 项目树

默认延迟加载先查项目，再为每个项目查设备。即使项目没有设备，第一次访问集合也需要查询。用 `selectinload(Project.devices)` 后，本课小数据集预期只有两条业务 SELECT，一条查项目，一条按项目 ID 批量查设备。没有设备的项目序列化为 `devices: []`。

在已设置 DATABASE_URL 的课程 CMD 中运行 `python inspect_project_tree.py`，用 `echo=True` 比较更改前后的 SELECT 数。用 `python -m uvicorn api:app --host 127.0.0.1 --port 8000` 启动服务，打开 `GET /projects/tree` 验证项目与设备归属。

## 设备分页

- 生成并审查迁移：`python -m alembic revision --autogenerate -m "add device created_at"`。核对带时区、数据库默认值 now()、NOT NULL，再执行 `python -m alembic upgrade head`。已有行获得的是迁移事务时间，历史创建时间无法由此还原。
- `GET /api/v1/projects/{project_id}/devices` 按项目查询，按 created_at DESC、id DESC 排序。OFFSET 为 (page - 1) × page_size。page_size 上限为 100。
- q 按设备编码做不区分大小写的子串匹配。总数和列表共用筛选条件。total 在分页前计算，items 取当前页。
- 固定数据下，若顺序为 9、7，每页一条，第二页是 7。若第一页后插入排在最前面的 10，第二页 OFFSET 1 会再次读到 9。

## 验收预期

| 操作 | 预期 |
|---|---|
| 项目树 SQL 日志 | 延迟加载 1 + N 条业务 SELECT，小数据集批量加载 2 条 |
| 项目 A 两页，每页一条 | ID 不同，同时间时较大 ID 在前 |
| q=SENSOR，第一页每页一条 | total=2，items 一条 |
| q=SENSOR，第三页每页一条 | total=2，items=[] |
| q=no-such-device | 200，total=0，items=[] |
| page_size=101 | 422，错误指向 page_size |
| 项目 ID 不存在 | 404 |
| 项目存在但没有设备 | 200，total=0，items=[] |

## 实际观察与排错

- 截图显示把“项目ID”原样放进 URL 后出现 int_parsing。换成数据库里查到的整数 ID。
- 后续截图显示项目 1 的第一页返回 sensor-02，但只有 items。检查返回字典包含 total，保存并重启 Uvicorn，再用无匹配关键词验证筛选。
- SQL 条数、修正后的筛选响应和其余边界检查未收到实际输出，以上表格记录的是验收预期。

## 自测

1. 空项目的 ORM 设备集合是什么？空列表 []。LEFT JOIN 的设备列可能显示 NULL。
2. 创建时间相同时会自动按 ID 排序吗？需要显式写 id DESC。
3. page=3 且 page_size=2 跳过几条？4 条。
4. 两台设备匹配，第三页每页一条，total 和 items 是什么？2 和 []。
5. 顺序是 9、7，数据不变时第二页是哪台？7。若两次请求间插入排在最前面的 10，第二页会重复返回 9。
