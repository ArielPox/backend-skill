from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


project_dir = Path(__file__).resolve().parent
config = Config(str(project_dir / "alembic.ini"))
config.set_main_option(
    "script_location",
    str(project_dir / "migrations"),
)

branch_revisions = ("47ab6a8e1bae", "69c933827e00")

# 确认当前末端恰好是本次实验的两个分支。
scripts = ScriptDirectory.from_config(config)
if set(scripts.get_heads()) != set(branch_revisions):
    raise RuntimeError("当前迁移末端与实验预期不同，请检查现有版本")

# 创建一个同时依赖两个分支的合并版本。
merged = command.merge(
    config,
    revisions=branch_revisions,
    message="merge project description and device location",
)

# 重新读取迁移文件，验证合并后的结构。
scripts = ScriptDirectory.from_config(config)
heads = scripts.get_heads()
merge_revision = scripts.get_revision(merged.revision)

print(f"合并版本：{merge_revision.revision}")
print(f"上一版本：{merge_revision.down_revision}")
print(f"当前 head 数量：{len(heads)}")

assert heads == [merged.revision]
assert set(merge_revision.down_revision) == set(branch_revisions)

print("迁移分支合并验收通过")
