from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from settings import DATABASE_URL


# 根据当前脚本的位置找到项目配置和迁移目录。
project_dir = Path(__file__).resolve().parent
config = Config(str(project_dir / "alembic.ini"))
config.set_main_option(
    "script_location",
    str(project_dir / "migrations"),
)

engine = create_engine(DATABASE_URL)

# 合并版本及其两个前置分支。
merge_revision = "c5441c214269"
branch_revisions = {"47ab6a8e1bae", "69c933827e00"}

# 第一步：读取数据库实际执行到的迁移版本。
with engine.connect() as connection:
    context = MigrationContext.configure(connection)
    before = context.get_current_heads()

print(f"降级前数据库版本：{sorted(before)}")

# 必须从合并版本开始，避免重复运行时继续撤销字段迁移。
if set(before) != {merge_revision}:
    raise RuntimeError(
        "数据库当前未处于合并版本 c5441c214269，请根据上面的版本输出检查"
    )

# 第二步：撤销一个迁移步骤。
# 本次执行合并版本的 downgrade()，其中只有 pass。
command.downgrade(config, "47ab6a8e1bae")

# 第三步：重新读取数据库版本，确认回到两个分支末端。
with engine.connect() as connection:
    context = MigrationContext.configure(connection)
    after = context.get_current_heads()

print(f"降级后数据库版本：{sorted(after)}")
assert set(after) == branch_revisions, "数据库没有回到预期的两个分支"

# 第四步：查询数据库实际表结构，确认两个字段仍然存在。
inspector = inspect(engine)

for table_name, column_name in [
    ("projects", "description"),
    ("devices", "location"),
]:
    columns = {column["name"] for column in inspector.get_columns(table_name)}

    assert column_name in columns, f"{table_name}.{column_name} 缺失"
    print(f"{table_name}.{column_name} 仍然存在")

print("撤销合并版本验收通过")
