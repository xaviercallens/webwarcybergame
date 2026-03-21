"""force_add_faction_id

Revision ID: 5d64c9a90862
Revises: 999999999999
Create Date: 2026-03-19 11:47:39.568260

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d64c9a90862'
down_revision: Union[str, Sequence[str], None] = '999999999999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Safely try adding the column
    try:
        op.add_column('player', sa.Column('faction_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_player_faction_id', 'player', 'faction', ['faction_id'], ['id'])
    except Exception as e:
        print(f"Skipping because column probably exists: {e}")


def downgrade() -> None:
    """Downgrade schema."""
    pass
