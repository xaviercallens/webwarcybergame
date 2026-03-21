"""Fix player table by adding missing columns if they don't exist

Revision ID: 999999999999
Revises: ea68d04c5305
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '999999999999'
down_revision = 'ea68d04c5305'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Check if 'player' table exists before inspecting columns
    tables = inspector.get_table_names()
    if 'player' not in tables:
        return
        
    columns = [col['name'] for col in inspector.get_columns('player')]

    if 'faction_id' not in columns:
        op.add_column('player', sa.Column('faction_id', sa.Integer(), nullable=True))
        # Add foreign key constraint safely
        op.create_foreign_key('fk_player_faction_id', 'player', 'faction', ['faction_id'], ['id'])
        
    if 'xp' not in columns:
        op.add_column('player', sa.Column('xp', sa.Integer(), server_default='0', nullable=False))
    if 'rank' not in columns:
        op.add_column('player', sa.Column('rank', sa.String(), server_default='Rookie', nullable=False))
    if 'wins' not in columns:
        op.add_column('player', sa.Column('wins', sa.Integer(), server_default='0', nullable=False))
    if 'losses' not in columns:
        op.add_column('player', sa.Column('losses', sa.Integer(), server_default='0', nullable=False))
    if 'win_streak' not in columns:
        op.add_column('player', sa.Column('win_streak', sa.Integer(), server_default='0', nullable=False))
    if 'best_streak' not in columns:
        op.add_column('player', sa.Column('best_streak', sa.Integer(), server_default='0', nullable=False))

def downgrade() -> None:
    pass
