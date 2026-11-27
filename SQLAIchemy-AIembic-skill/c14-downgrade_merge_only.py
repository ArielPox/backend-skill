from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from settings import DATABASE_URL


project_dir = Path(__file__).resolve().parent
config = Config(str(project_dir / "alembic.ini"))
config.set_main_option(
    "script_location",
    str(project_dir / "migrations"),
)

merge_revision = "c5441c214269"
branch_revisions = {"47ab6a8e1bae", "69c933827e00"}

engine = create_engine(DATABASE_URL)

# 确认起点，防止重复运行时继续撤销字段迁移。
with engine.connect() as connection:
    current = MigrationContext.configure(connection).get_current_heads()

print(f"降级前数据库版本：{list(current)}")

if set(current) != {merge_revision}:
    raise RuntimeError("本实验要求数据库当前位于合并版本，请检查版本输出")

# 从当前合并版本向下降一个迁移步骤。
command.downgrade(config, "-1")

# 重新读取表结构，确认两个分支创建的字段仍然存在。
inspector = inspect(engine)

for table_name, column_name in [
    ("projects", "description"),
    ("devices", "location"),
]:
    column_names = {column["name"] for column in inspector.get_columns(table_name)}
    assert column_name in column_names, f"{table_name}.{column_name} 缺失"
    print(f"{table_name}.{column_name} 仍然存在")

with engine.connect() as connection:
    current = MigrationContext.configure(connection).get_current_heads()

print(f"降级后数据库版本：{sorted(current)}")
assert set(current) == branch_revisions

# 迁移文件仍保留合并版本，可以用于后续重新升级。
script_heads = ScriptDirectory.from_config(config).get_heads()
print(f"迁移文件的 heads：{script_heads}")
assert script_heads == [merge_revision]

print("撤销合并版本验收通过")
