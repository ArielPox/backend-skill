from pathlib import Path

from alembic import command
from alembic.config import Config


project_dir = Path(__file__).resolve().parent

config = Config(str(project_dir / "alembic.ini"))
config.set_main_option(
    "script_location",
    str(project_dir / "migrations"),
)

# 根据模型与当前数据库的差异，生成迁移文件。
revision = command.revision(
    config,
    message="create users and roles",
    autogenerate=True,
)

print(f"生成的迁移文件：{revision.path}")
print(f"新版本号：{revision.revision}")
print(f"上一版本：{revision.down_revision}")