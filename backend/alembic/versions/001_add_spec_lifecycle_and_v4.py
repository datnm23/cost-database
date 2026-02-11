"""Add spec lifecycle, v4.0 codes, and audit trail

Revision ID: 001
Revises: None
Create Date: 2026-02-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # 1. ALTER master_work_items: add spec lifecycle + v4.0 columns
    # ----------------------------------------------------------------
    op.add_column('master_work_items', sa.Column(
        'spec_status',
        sa.Enum('draft', 'detailed', 'final', name='spec_status_enum'),
        nullable=False,
        server_default='draft',
        comment='Spec lifecycle stage',
    ))
    op.add_column('master_work_items', sa.Column(
        'spec_source',
        sa.Enum('default', 'boq', 'drawing', 'as_built', name='spec_source_enum'),
        nullable=False,
        server_default='default',
        comment='Where the spec data came from',
    ))
    op.add_column('master_work_items', sa.Column(
        'spec_confidence', sa.Float, nullable=False, server_default='0',
        comment='Confidence 0.0-1.0 based on source',
    ))
    op.add_column('master_work_items', sa.Column(
        'spec_completeness', sa.Float, nullable=False, server_default='0',
        comment='Weighted completeness 0.0-1.0',
    ))
    op.add_column('master_work_items', sa.Column(
        'sec_code_v4', sa.String(30), nullable=True,
        comment='v4.0 code e.g. A.CV.CON.POUR.COL',
    ))
    op.add_column('master_work_items', sa.Column(
        'item_table_type',
        sa.Enum('A', 'M', 'L', 'E', name='item_table_type_enum'),
        nullable=False,
        server_default='A',
        comment='Which v4.0 table: Activity/Material/Labour/Equipment',
    ))
    op.add_column('master_work_items', sa.Column(
        'work_code_legacy', sa.String(50), nullable=True,
        comment='Original S-prefix work code before v4.0 migration',
    ))

    # Indexes on new columns
    op.create_index('idx_master_spec_status', 'master_work_items', ['spec_status'])
    op.create_index('idx_master_sec_code_v4', 'master_work_items', ['sec_code_v4'], unique=True)
    op.create_index('idx_master_table_type', 'master_work_items', ['item_table_type'])

    # ----------------------------------------------------------------
    # 2. ALTER line_items: add sec_code_v4
    # ----------------------------------------------------------------
    op.add_column('line_items', sa.Column(
        'sec_code_v4', sa.String(30), nullable=True,
        comment='Mapped v4.0 code e.g. A.CV.CON.POUR.COL',
    ))

    # ----------------------------------------------------------------
    # 3. CREATE TABLE spec_change_logs
    # ----------------------------------------------------------------
    op.create_table(
        'spec_change_logs',
        sa.Column('log_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('master_id', sa.Integer,
                   sa.ForeignKey('master_work_items.master_id', ondelete='CASCADE'),
                   nullable=False, index=True),
        sa.Column('field_name', sa.String(50), nullable=False,
                   comment='Field that changed (spec_grade, spec_material, etc.)'),
        sa.Column('old_value', sa.Text, nullable=True),
        sa.Column('new_value', sa.Text, nullable=True),
        sa.Column('old_status', sa.String(20), nullable=True, comment='Previous spec_status'),
        sa.Column('new_status', sa.String(20), nullable=True, comment='New spec_status'),
        sa.Column('change_source', sa.String(20), nullable=False, server_default='manual',
                   comment='Source: manual, boq, drawing, as_built, default, system'),
        sa.Column('changed_by', sa.Integer,
                   sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('changed_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
    )

    # ----------------------------------------------------------------
    # 4. CREATE TABLE sec_codes_v4
    # ----------------------------------------------------------------
    op.create_table(
        'sec_codes_v4',
        sa.Column('code', sa.String(30), primary_key=True,
                   comment='Full code e.g. A.CV.CON.POUR.COL'),
        sa.Column('table_type',
                   sa.Enum('A', 'M', 'L', 'E', name='sec_v4_table_type'),
                   nullable=False,
                   comment='A=Activity, M=Material, L=Labour, E=Equipment'),
        sa.Column('discipline', sa.String(5), nullable=False,
                   comment='L1: CV, AR, EL, PL, ME, FP, LV, VT, LA, EX, PM'),
        sa.Column('group_code', sa.String(5), nullable=False,
                   comment='L2: CON, RBR, PIP, FWK, EXC, PIL...'),
        sa.Column('type_code', sa.String(5), nullable=False,
                   comment='L3: POUR, FABR, INST, FORM... (method/action)'),
        sa.Column('spec_code', sa.String(5), nullable=False,
                   comment='L4: COL, FND, GEN, SUP, BEM, SLB...'),
        sa.Column('name_vi', sa.String(200), nullable=True, comment='Vietnamese name'),
        sa.Column('name_en', sa.String(200), nullable=True, comment='English name'),
        sa.Column('unit', sa.String(20), nullable=True, comment='Default unit'),
        sa.Column('keywords_vi', sa.Text, nullable=True,
                   comment='Vietnamese keywords for fuzzy matching (JSON)'),
        sa.Column('keywords_en', sa.Text, nullable=True,
                   comment='English keywords for fuzzy matching (JSON)'),
        sa.Column('waste_percent', sa.Float, server_default='0',
                   comment='Default waste percentage'),
        sa.Column('is_active', sa.Boolean, server_default='1', nullable=False),
    )
    op.create_index('idx_sec_v4_table_type', 'sec_codes_v4', ['table_type'])
    op.create_index('idx_sec_v4_discipline', 'sec_codes_v4', ['discipline'])
    op.create_index('idx_sec_v4_group', 'sec_codes_v4', ['group_code'])
    op.create_index('idx_sec_v4_type', 'sec_codes_v4', ['type_code'])

    # ----------------------------------------------------------------
    # 5. CREATE TABLE activity_bom
    # ----------------------------------------------------------------
    op.create_table(
        'activity_bom',
        sa.Column('bom_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('activity_code', sa.String(30),
                   sa.ForeignKey('sec_codes_v4.code', ondelete='CASCADE'),
                   nullable=False, index=True,
                   comment='Activity code (A.* prefix)'),
        sa.Column('resource_code', sa.String(30),
                   sa.ForeignKey('sec_codes_v4.code', ondelete='CASCADE'),
                   nullable=False, index=True,
                   comment='Resource code (M.*/L.*/E.* prefix)'),
        sa.Column('resource_type',
                   sa.Enum('M', 'L', 'E', name='bom_resource_type'),
                   nullable=False,
                   comment='M=Material, L=Labour, E=Equipment'),
        sa.Column('quantity_factor', sa.Float, nullable=False, server_default='1',
                   comment='Resource qty per unit of activity'),
        sa.Column('notes', sa.Text, nullable=True),
    )
    op.create_index('idx_bom_activity_resource', 'activity_bom',
                     ['activity_code', 'resource_code'], unique=True)

    # ----------------------------------------------------------------
    # 6. Data migration: populate spec_completeness for existing rows
    # ----------------------------------------------------------------
    # Compute completeness for existing master items
    op.execute("""
        UPDATE master_work_items SET
            spec_completeness = (
                CASE WHEN spec_category IS NOT NULL AND spec_category != '' THEN 0.25 ELSE 0 END +
                CASE WHEN spec_material IS NOT NULL AND spec_material != '' THEN 0.25 ELSE 0 END +
                CASE WHEN spec_grade IS NOT NULL AND spec_grade != '' THEN 0.30 ELSE 0 END +
                CASE WHEN spec_dimension IS NOT NULL AND spec_dimension != '' THEN 0.20 ELSE 0 END
            ),
            spec_confidence = CASE
                WHEN spec_grade IS NOT NULL AND spec_grade != '' THEN 0.5
                ELSE 0.3
            END,
            spec_source = CASE
                WHEN spec_grade IS NOT NULL AND spec_grade != '' THEN 'boq'
                ELSE 'default'
            END
    """)

    # Copy work_code → work_code_legacy for existing rows
    op.execute("""
        UPDATE master_work_items
        SET work_code_legacy = work_code
        WHERE work_code_legacy IS NULL
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('activity_bom')
    op.drop_table('sec_codes_v4')
    op.drop_table('spec_change_logs')

    # Remove line_items column
    op.drop_column('line_items', 'sec_code_v4')

    # Remove master_work_items columns and indexes
    op.drop_index('idx_master_table_type', table_name='master_work_items')
    op.drop_index('idx_master_sec_code_v4', table_name='master_work_items')
    op.drop_index('idx_master_spec_status', table_name='master_work_items')

    op.drop_column('master_work_items', 'work_code_legacy')
    op.drop_column('master_work_items', 'item_table_type')
    op.drop_column('master_work_items', 'sec_code_v4')
    op.drop_column('master_work_items', 'spec_completeness')
    op.drop_column('master_work_items', 'spec_confidence')
    op.drop_column('master_work_items', 'spec_source')
    op.drop_column('master_work_items', 'spec_status')
