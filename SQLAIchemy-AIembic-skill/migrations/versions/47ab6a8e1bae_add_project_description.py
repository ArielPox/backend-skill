"""add project description

Revision ID: 47ab6a8e1bae
Revises: ba0b8f64f297
Create Date: 2026-11-20 19:22:53.810404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47ab6a8e1bae'
down_revision: Union[str, None] = 'ba0b8f64f297'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
