import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from settings import DATABASE_URL


project_dir = Path(__file__).resolve().parent
source_url = make_url(DATABASE_URL)

demo_database = "p29_lab_branch_b_demo"
demo_url = source_url.set(database=demo_database)

# 创建用于分支升级验证的独立数据库。
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
        connection.execute(text('CREATE DATABASE "p29_lab_branch_b_demo"'))

admin_engine.dispose()

# 所有迁移命令都连接这个实验库。
migration_env = os.environ.copy()
migration_env["DATABASE_URL"] = demo_url.render_as_string(hide_password=False)

engine = create_engine(demo_url)


def run_upgrade(target):
    # 使用当前 VS Code 选中的 Python，执行指定目标的升级。
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", target],
        cwd=project_dir,
        env=migration_env,
        check=True,
    )


def read_versions():
    with engine.connect() as connection:
        return (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalars()
            .all()
        )


def column_exists(table_name, column_name):
    # 每次重新创建 Inspector，读取当前表结构。
    return any(
        column["name"] == column_name
        for column in inspect(engine).get_columns(table_name)
    )


# 核对已有实验库的状态，便于失败后接着执行。
if inspect(engine).has_table("alembic_version"):
    versions = read_versions()
    if versions and versions != ["69c933827e00"]:
        raise RuntimeError(f"实验库当前版本为 {versions}，本次需要空库或甲分支状态")


# 第一阶段：明确指定乙分支作为升级目标。
run_upgrade("69c933827e00")

assert read_versions() == ["69c933827e00"]
assert not column_exists("projects", "description")
assert column_exists("devices", "location")

print("乙分支验收通过：location 存在，description 缺失")

# 第二阶段：升级到合并末端，补齐尚未执行的甲分支。
run_upgrade("head")

assert read_versions() == ["c5441c214269"]
assert column_exists("projects", "description")
assert column_exists("devices", "location")

print("合并验收通过：description 和 location 都存在")
print(f"数据库当前版本：{read_versions()}")

engine.dispose()
