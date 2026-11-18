# FastAPI Agent 项目结构

```text
fastapi_agent_project/
├── .gitignore                      # git忽略配置（重点：.env、数据库密码、日志）
├── requirements.txt                # 全部依赖包
├── Dockerfile                      # 生产镜像构建
├── docker-compose.yml              # 本地开发专用
├── alembic.ini                     # Alembic配置（注释掉写死url，读环境变量）
├── alembic/                        # Alembic迁移目录
│   ├── versions/                   # 迁移脚本版本文件
│   ├── env.py                      # 适配环境变量读取DB_URI
│   └── script.py.mako
├── .env.dev                        # 本地开发环境变量（不上git）
├── .env.prod                       # 生产环境变量（仅服务器存放，不上git）
└── app/
    ├── __init__.py
    ├── main.py                     # FastAPI入口 + lifespan生命周期钩子
    ├── config.py                   # 全局配置，读取所有环境变量
    ├── api/                        # 接口路由模块
    │   ├── __init__.py
    │   ├── dependencies.py         # 公共依赖（数据库session、用户鉴权）
    │   ├── routes/
    │   │   ├── __init__.py
    │   │   ├── agent_chat.py       # Agent问答接口
    │   │   └── user.py             # 用户相关接口示例
    ├── db/                         # 数据库层
    │   ├── __init__.py
    │   ├── mysql.py                # SQLAlchemy引擎、SessionLocal、get_db依赖
    │   ├── mongo.py                # pymongo连接、索引、mongo迁移脚本、会话CRUD
    │   └── models/                 # SQLAlchemy ORM模型（MySQL表）
    │       ├── __init__.py
    │       └── base.py             # Base = declarative_base()
    ├── agent/                      # 千问Agent业务模块
    │   ├── __init__.py
    │   ├── qwen_agent.py           # 千问Agent封装、对话调用逻辑
    │   └── tools/                  # Agent自定义工具（Function Call，如果有）
    │       ├── __init__.py
    │       └── custom_tools.py
    ├── schemas/                    # Pydantic请求/响应模型
    │   ├── __init__.py
    │   ├── agent_schema.py
    │   └── user_schema.py
    └── utils/                      # 通用工具
        ├── __init__.py
        └── common.py
```
