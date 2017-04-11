"""Add unique constraints

Revision ID: 0868747e62ff
Revises: e60a77e44da8
Create Date: 2017-04-11 16:10:42.109777

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0868747e62ff'
down_revision = 'e60a77e44da8'
branch_labels = ()
depends_on = None

def upgrade():
    op.create_unique_constraint(None, 'package', ['id'])
    op.create_unique_constraint(None, 'package_result', ['id'])
    op.create_unique_constraint(None, 'platform', ['id'])
    op.create_unique_constraint(None, 'release', ['id'])
    op.create_unique_constraint(None, 'release_metadata', ['id'])
    op.create_unique_constraint(None, 'release_note', ['id'])


def downgrade():
    op.drop_constraint(None, 'release_note', type_='unique')
    op.drop_constraint(None, 'release_metadata', type_='unique')
    op.drop_constraint(None, 'release', type_='unique')
    op.drop_constraint(None, 'platform', type_='unique')
    op.drop_constraint(None, 'package_result', type_='unique')
    op.drop_constraint(None, 'package', type_='unique')
