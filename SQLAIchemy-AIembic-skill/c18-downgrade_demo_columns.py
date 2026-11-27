import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from settings import DATABASE_URL


project_dir = Path(__file__).resolve().parent

# 所有查询和迁移都显式使用独立实验库。
demo_database = "p29_lab_rollback_demo"
demo_url = make_url(DATABASE_URL).set(database=demo_database)
engine = create_engine(demo_url)

with engine.connect() as connection:
    actual_database = connection.execute(
        text("SELECT current_database()")
    ).scalar_one()

    versions = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalars().all()

assert actual_database == demo_database
assert versions == ["c5441c214269"], f"起点版本不符合预期：{versions}"

print(f"实验数据库：{actual_database}")
print(f"降级前版本：{versions}")

# 为迁移进程指定实验库，退回两个字段分支的共同起点。
migration_env = os.environ.copy()
migration_env["DATABASE_URL"] = demo_url.render_as_string(
    hide_password=False
)

subprocess.run(
    [
        sys.executable,
        "-m",
        "alembic",
        "downgrade",
        "ba0b8f64f297",
    ],
    cwd=project_dir,
    env=migration_env,
    check=True,
)

# 查询实际结构，验证两个字段都已被删除。
inspector = inspect(engine)

for table_name, column_name in [
    ("projects", "description"),
    ("devices", "location"),
]:
    columns = {
        column["name"]
        for column in inspector.get_columns(table_name)
    }

    assert column_name not in columns, f"{table_name}.{column_name} 仍然存在"
    print(f"{table_name}.{column_name} 已删除")

# 使用仍然存在的列查询样本，避免 ORM 自动选择已经删除的字段。
with engine.connect() as connection:
    sample = connection.execute(
        text("""
            SELECT p.code AS project_code, d.code AS device_code
            FROM projects AS p
            JOIN devices AS d ON d.project_id = p.id
            WHERE p.code = :project_code
              AND d.code = :device_code
        """),
        {
            "project_code": "ROLLBACK-DEMO",
            "device_code": "sensor-demo",
        },
    ).one()

    versions = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalars().all()

assert versions == ["ba0b8f64f297"]

print(f"项目仍然存在：{sample.project_code}")
print(f"设备仍然存在：{sample.device_code}")
print(f"降级后版本：{versions}")

engine.dispose()
print("字段降级验收通过")