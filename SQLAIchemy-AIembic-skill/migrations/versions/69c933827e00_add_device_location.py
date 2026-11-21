"""add device location

Revision ID: 69c933827e00
Revises: ba0b8f64f297
Create Date: 2026-11-20 19:22:53.834665

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "69c933827e00"
down_revision: Union[str, None] = "ba0b8f64f297"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 历史设备的位置未知时允许为空。
    op.add_column(
        "devices",
        sa.Column("location", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    # 撤销该版本时删除位置列。
    op.drop_column("devices", "location")
