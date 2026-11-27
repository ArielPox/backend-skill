import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from settings import DATABASE_URL


project_dir = Path(__file__).resolve().parent

# 升级和验收都使用独立实验库。
demo_database = "p29_lab_rollback_demo"
demo_url = make_url(DATABASE_URL).set(database=demo_database)
engine = create_engine(demo_url)

with engine.connect() as connection:
    actual_database = connection.execute(
        text("SELECT current_database()")
    ).scalar_one()

    before = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalars().all()

assert actual_database == demo_database
assert before == ["ba0b8f64f297"], f"起点版本不符合预期：{before}"

print(f"实验数据库：{actual_database}")
print(f"升级前版本：{before}")

# 重新执行两个字段迁移及合并迁移。
migration_env = os.environ.copy()
migration_env["DATABASE_URL"] = demo_url.render_as_string(
    hide_password=False
)

subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=project_dir,
    env=migration_env,
    check=True,
)

# 检查数据库中的两个字段已经重新创建。
inspector = inspect(engine)

for table_name, column_name in [
    ("projects", "description"),
    ("devices", "location"),
]:
    columns = {
        column["name"]
        for column in inspector.get_columns(table_name)
    }

    assert column_name in columns, f"{table_name}.{column_name} 缺失"
    print(f"{table_name}.{column_name} 已重新创建")

# 直接查询升级后的值，观察迁移本身产生的结果。
with engine.connect() as connection:
    sample = connection.execute(
        text("""
            SELECT
                p.code AS project_code,
                p.description,
                d.code AS device_code,
                d.location
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

    after = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalars().all()

print(f"项目编码：{sample.project_code}")
print(f"项目描述：{sample.description}")
print(f"设备编码：{sample.device_code}")
print(f"设备位置：{sample.location}")
print(f"升级后版本：{after}")

assert sample.description is None, "描述值与本实验预期不一致"
assert sample.location is None, "位置值与本实验预期不一致"
assert after == ["c5441c214269"]

engine.dispose()
print("字段重新创建、原值丢失的对照验收通过")