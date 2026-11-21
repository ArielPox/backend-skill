"""add project description

Revision ID: 47ab6a8e1bae
Revises: ba0b8f64f297
Create Date: 2026-11-20 19:22:53.810404

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "47ab6a8e1bae"
down_revision: Union[str, None] = "ba0b8f64f297"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 允许历史项目暂时缺少描述。
    op.add_column(
        "projects",
        sa.Column("description", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # 撤销该版本时删除描述列，该列已保存的内容也会被删除。
    op.drop_column("projects", "description")
