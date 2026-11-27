import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from settings import DATABASE_URL


project_dir = Path(__file__).resolve().parent
source_url = make_url(DATABASE_URL)

# 本实验使用单独的数据库。
demo_database = "p29_lab_rollback_demo"
demo_url = source_url.set(database=demo_database)

# PostgreSQL 创建数据库需要在事务之外执行。
admin_engine = create_engine(
    source_url.set(database="postgres"),
    isolation_level="AUTOCOMMIT",
)

with admin_engine.connect() as connection:
    exists = connection.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :name"),
        {"name": demo_database},
    ).scalar_one_or_none()

    if exists is None:
        connection.execute(
            text('CREATE DATABASE "p29_lab_rollback_demo"')
        )
        print(f"已创建实验库：{demo_database}")
    else:
        print(f"使用已有实验库：{demo_database}")

admin_engine.dispose()

# 为迁移进程指定实验库地址。
# settings.py 的 override=False 使这个地址优先于 local.env。
migration_env = os.environ.copy()
migration_env["DATABASE_URL"] = demo_url.render_as_string(
    hide_password=False
)

# 使用当前 VS Code 选中的 Python 运行 Alembic。
subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=project_dir,
    env=migration_env,
    check=True,
)

# 直接连接实验库，检查实际库名和版本。
demo_engine = create_engine(demo_url)

with demo_engine.connect() as connection:
    actual_database = connection.execute(
        text("SELECT current_database()")
    ).scalar_one()

    versions = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalars().all()

print(f"实际连接数据库：{actual_database}")
print(f"数据库迁移版本：{versions}")

assert actual_database == demo_database
assert versions == ["c5441c214269"]

demo_engine.dispose()
print("独立实验库准备完成")