"""
Migration script to add 'status' column to email_communications table.
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('email_communications', sa.Column('status', sa.String(length=50), nullable=True))

def downgrade():
    op.drop_column('email_communications', 'status')
