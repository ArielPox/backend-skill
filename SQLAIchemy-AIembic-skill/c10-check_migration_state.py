from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

from settings import DATABASE_URL


# 根据脚本位置定位配置，避免受到终端当前目录影响。
project_dir = Path(__file__).resolve().parent
config = Config(str(project_dir / "alembic.ini"))
config.set_main_option(
    "script_location",
    str(project_dir / "migrations"),
)

# 读取本地迁移文件中的所有末端版本。
scripts = ScriptDirectory.from_config(config)
script_heads = scripts.get_heads()
print(f"迁移文件的 heads：{script_heads}")

# 读取当前连接数据库记录的迁移版本。
engine = create_engine(DATABASE_URL)
with engine.connect() as connection:
    context = MigrationContext.configure(connection)
    database_heads = context.get_current_heads()
    print(f"数据库当前版本：{list(database_heads)}")

assert len(script_heads) == 1, "当前存在多个迁移末端，请检查输出"
assert set(database_heads) == set(script_heads), "数据库与迁移文件版本不一致"

print("起点验收通过")
