from pathlib import Path

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

# 本次沿用应用配置，检查应用实际使用的数据库。
engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    database_name = connection.execute(
        text("SELECT current_database()")
    ).scalar_one()

    database_versions = set(
        MigrationContext.configure(connection).get_current_heads()
    )

print(f"实际数据库：{database_name}")
assert database_name == "p29_lab", "连接目标与主实验库不一致，请检查配置"

# 比较数据库版本和代码中的迁移末端。
script_heads = set(ScriptDirectory.from_config(config).get_heads())

print(f"数据库版本：{sorted(database_versions)}")
print(f"迁移文件末端：{sorted(script_heads)}")

assert len(script_heads) == 1, "迁移文件存在多个末端"
assert database_versions == script_heads, "数据库与迁移文件版本不一致"

# 检查后续接口实验需要的字段。
required_columns = {
    "projects": {"id", "code", "name", "description"},
    "devices": {
        "id", "project_id", "code", "name",
        "created_at", "last_seen_at", "location",
    },
    "alarms": {"id", "device_id", "status", "message", "occurred_at"},
}

inspector = inspect(engine)
tables = set(inspector.get_table_names())

for table_name, expected_columns in required_columns.items():
    assert table_name in tables, f"缺少表：{table_name}"

    actual_columns = {
        column["name"]
        for column in inspector.get_columns(table_name)
    }
    missing = expected_columns - actual_columns
    assert not missing, f"{table_name} 缺少字段：{sorted(missing)}"

    print(f"{table_name} 结构检查通过")

# 确认有可供后续查询验收使用的实验数据。
with engine.connect() as connection:
    counts = connection.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM projects) AS projects,
            (SELECT COUNT(*) FROM devices) AS devices,
            (SELECT COUNT(*) FROM alarms) AS alarms
    """)).one()

for table_name, count in counts._mapping.items():
    print(f"{table_name} 记录数：{count}")
    assert count > 0, f"{table_name} 暂无数据，需要先准备查询样本"

engine.dispose()
print("综合验收基础检查通过")