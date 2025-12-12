"""merge branches

Revision ID: e712f3443d94
Revises: a89cac7ecb0b, g2b3c4d5e6f7
Create Date: 2025-12-12 14:48:26.364700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e712f3443d94'
down_revision: Union[str, None] = ('a89cac7ecb0b', 'g2b3c4d5e6f7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

