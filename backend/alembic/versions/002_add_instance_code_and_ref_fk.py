"""Add instance_code column and convert sec_code_v4 to FK reference

Revision ID: 002
Revises: 001
Create Date: 2026-02-11

Changes:
- Add instance_code column (unique, nullable) to master_work_items
- Remove UNIQUE constraint on sec_code_v4 (now a 1:N reference code)
- Add FK constraint sec_code_v4 → sec_codes_v4.code
- Migrate data: instance_code = sec_code_v4 + '-001' for existing records
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # 1. Add instance_code column
    # ----------------------------------------------------------------
    op.add_column('master_work_items', sa.Column(
        'instance_code', sa.String(35), nullable=True,
        comment='Unique instance e.g. A.CV.CON.POUR.COL-001',
    ))
    op.create_index('idx_master_instance_code', 'master_work_items',
                     ['instance_code'], unique=True)

    # ----------------------------------------------------------------
    # 2. Migrate data: instance_code = sec_code_v4 + '-001'
    # ----------------------------------------------------------------
    op.execute("""
        UPDATE master_work_items
        SET instance_code = CONCAT(sec_code_v4, '-001')
        WHERE sec_code_v4 IS NOT NULL
          AND instance_code IS NULL
    """)

    # ----------------------------------------------------------------
    # 3. Remove UNIQUE constraint on sec_code_v4
    #    (drop old unique index, create non-unique index)
    # ----------------------------------------------------------------
    op.drop_index('idx_master_sec_code_v4', table_name='master_work_items')
    op.create_index('idx_master_sec_code_v4', 'master_work_items',
                     ['sec_code_v4'], unique=False)

    # ----------------------------------------------------------------
    # 4. Add FK constraint sec_code_v4 → sec_codes_v4.code
    # ----------------------------------------------------------------
    op.create_foreign_key(
        'fk_master_sec_code_v4',
        'master_work_items', 'sec_codes_v4',
        ['sec_code_v4'], ['code'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    # Drop FK
    op.drop_constraint('fk_master_sec_code_v4', 'master_work_items',
                        type_='foreignkey')

    # Restore unique index on sec_code_v4
    op.drop_index('idx_master_sec_code_v4', table_name='master_work_items')
    op.create_index('idx_master_sec_code_v4', 'master_work_items',
                     ['sec_code_v4'], unique=True)

    # Drop instance_code
    op.drop_index('idx_master_instance_code', table_name='master_work_items')
    op.drop_column('master_work_items', 'instance_code')
