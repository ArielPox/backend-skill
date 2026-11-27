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

base_revision = "ba0b8f64f297"

# 确认仍位于本实验起点，也能避免重复运行时再次生成迁移。
scripts = ScriptDirectory.from_config(config)
if scripts.get_heads() != [base_revision]:
    raise RuntimeError("迁移起点已经变化，请先查看现有迁移文件")

# 甲从共同起点创建自己的迁移。
revision_a = command.revision(
    config,
    message="add project description",
    head=base_revision,
)

# 创建甲的迁移后，共同起点已有后续版本。
# splice=True 允许从这个起点再创建乙的分支。
revision_b = command.revision(
    config,
    message="add device location",
    head=base_revision,
    splice=True,
)

# 重新读取目录，验证两条分支的结构。
scripts = ScriptDirectory.from_config(config)
heads = scripts.get_heads()

print(f"当前 head 数量：{len(heads)}")

for revision_id in heads:
    revision = scripts.get_revision(revision_id)
    print(f"迁移：{revision.doc}")
    print(f"  当前版本：{revision.revision}")
    print(f"  上一版本：{revision.down_revision}")
    assert revision.down_revision == base_revision

assert set(heads) == {revision_a.revision, revision_b.revision}
print("双分支创建验收通过")
