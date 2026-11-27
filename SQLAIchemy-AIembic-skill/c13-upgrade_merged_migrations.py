from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from settings import DATABASE_URL


project_dir = Path(__file__).resolve().parent
config = Config(str(project_dir / "alembic.ini"))
config.set_main_option(
    "script_location",
    str(project_dir / "migrations"),
)

scripts = ScriptDirectory.from_config(config)
heads = scripts.get_heads()
assert len(heads) == 1, f"预期只有一个 head，实际为 {heads}"

engine = create_engine(DATABASE_URL)

# 升级前记录现有数据数量。
count_sql = text("""
    SELECT
        (SELECT COUNT(*) FROM projects) AS project_count,
        (SELECT COUNT(*) FROM devices) AS device_count
""")

with engine.connect() as connection:
    before = tuple(connection.execute(count_sql).one())

print(f"升级前：项目 {before[0]} 条，设备 {before[1]} 条")

# 执行尚未应用的迁移，直到合并后的唯一末端。
command.upgrade(config, "head")

# 重新读取数据库实际结构，检查新字段及其可空性。
inspector = inspect(engine)

for table_name, column_name in [
    ("projects", "description"),
    ("devices", "location"),
]:
    columns = {column["name"]: column for column in inspector.get_columns(table_name)}

    assert column_name in columns, f"{table_name}.{column_name} 缺失"
    assert columns[column_name]["nullable"], f"{column_name} 应允许为空"
    print(f"{table_name}.{column_name} 已创建，允许为空")

# 检查升级后的记录数量和数据库版本。
with engine.connect() as connection:
    after = tuple(connection.execute(count_sql).one())
    context = MigrationContext.configure(connection)
    database_heads = context.get_current_heads()

print(f"升级后：项目 {after[0]} 条，设备 {after[1]} 条")
print(f"数据库当前版本：{list(database_heads)}")
print(f"迁移文件末端：{heads}")

assert after == before, "升级前后记录数量发生变化"
assert set(database_heads) == set(heads), "数据库版本尚未到达迁移末端"

print("合并升级验收通过")
