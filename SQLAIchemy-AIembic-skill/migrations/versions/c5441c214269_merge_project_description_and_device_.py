"""merge project description and device location

Revision ID: c5441c214269
Revises: 47ab6a8e1bae, 69c933827e00
Create Date: 2026-11-21 15:11:32.061444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5441c214269'
down_revision: Union[str, None] = ('47ab6a8e1bae', '69c933827e00')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
