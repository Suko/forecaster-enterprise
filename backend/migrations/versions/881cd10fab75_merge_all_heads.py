"""merge_all_heads

Revision ID: 881cd10fab75
Revises: 1a2b3c4d5e6f, c9152349e312
Create Date: 2025-12-12 15:57:03.472514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '881cd10fab75'
down_revision: Union[str, None] = ('1a2b3c4d5e6f', 'c9152349e312')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

