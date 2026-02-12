"""Add project_work_items and ai_training_logs tables

Revision ID: 004
Revises: 003
Create Date: 2026-02-12

Changes:
- Create project_work_items table (Zone 1 - Project Lake)
- Create ai_training_logs table (Zone 3 - Knowledge Base)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. Create project_work_items table
    # ================================================================
    op.create_table(
        'project_work_items',
        sa.Column('pwi_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.project_id'), nullable=False),
        sa.Column('file_id', sa.Integer(), sa.ForeignKey('boq_files.file_id'), nullable=False),
        sa.Column('line_item_id', sa.Integer(), sa.ForeignKey('line_items.line_item_id'), nullable=True),
        sa.Column('original_description', sa.Text(), nullable=False),
        sa.Column('normalized_description', sa.Text(), nullable=True),
        sa.Column('temp_code', sa.String(50), unique=True, nullable=False,
                  comment='Format: PRJ.{project_id}-TEMP-{seq:03d}'),
        sa.Column('master_work_item_id', sa.Integer(),
                  sa.ForeignKey('master_work_items.master_id'), nullable=True),
        sa.Column('wbs_context', sa.Text(), nullable=True,
                  comment='JSON: parent_title, section_path, neighbors, section_type'),
        sa.Column('wbs_level', sa.Integer(), default=0, nullable=True),
        sa.Column('quality_score', sa.Float(), default=0.0, nullable=True),
        sa.Column('gate_status',
                  sa.Enum('GREEN', 'YELLOW', 'RED', name='gate_status_enum'),
                  nullable=False, server_default='RED'),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('resolution_status',
                  sa.Enum('UNRESOLVED', 'MATCHED', 'APPROVED', 'MERGED', name='resolution_status_enum'),
                  nullable=False, server_default='UNRESOLVED'),
        sa.Column('resolved_by', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('ai_structured_output', sa.Text(), nullable=True,
                  comment='Cached LLM structured output JSON'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('idx_pwi_project', 'project_work_items', ['project_id'])
    op.create_index('idx_pwi_file', 'project_work_items', ['file_id'])
    op.create_index('idx_pwi_gate_status', 'project_work_items', ['gate_status'])
    op.create_index('idx_pwi_resolution', 'project_work_items', ['resolution_status'])
    op.create_index('idx_pwi_master', 'project_work_items', ['master_work_item_id'])
    op.create_index('idx_pwi_temp_code', 'project_work_items', ['temp_code'])

    # ================================================================
    # 2. Create ai_training_logs table
    # ================================================================
    op.create_table(
        'ai_training_logs',
        sa.Column('log_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('original_description', sa.Text(), nullable=False),
        sa.Column('normalized_description', sa.Text(), nullable=True),
        sa.Column('ai_suggestion', sa.Text(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_structured', sa.Text(), nullable=True,
                  comment='JSON: AI structured output'),
        sa.Column('human_choice', sa.Text(), nullable=True),
        sa.Column('human_master_id', sa.Integer(),
                  sa.ForeignKey('master_work_items.master_id'), nullable=True),
        sa.Column('action_type',
                  sa.Enum('ACCEPT', 'EDIT', 'REJECT', 'REMAP', name='training_action_enum'),
                  nullable=False),
        sa.Column('edit_distance', sa.Integer(), nullable=True,
                  comment='Levenshtein distance between AI suggestion and human choice'),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.project_id'), nullable=True),
        sa.Column('source_pwi_id', sa.Integer(),
                  sa.ForeignKey('project_work_items.pwi_id'), nullable=True),
        sa.Column('source_pending_id', sa.Integer(),
                  sa.ForeignKey('pending_master_items.pending_id'), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index('idx_training_action', 'ai_training_logs', ['action_type'])
    op.create_index('idx_training_project', 'ai_training_logs', ['project_id'])
    op.create_index('idx_training_created', 'ai_training_logs', ['created_at'])
    op.create_index('idx_training_master', 'ai_training_logs', ['human_master_id'])


def downgrade() -> None:
    # Drop ai_training_logs first (has FK to project_work_items)
    op.drop_index('idx_training_master', table_name='ai_training_logs')
    op.drop_index('idx_training_created', table_name='ai_training_logs')
    op.drop_index('idx_training_project', table_name='ai_training_logs')
    op.drop_index('idx_training_action', table_name='ai_training_logs')
    op.drop_table('ai_training_logs')

    # Drop project_work_items
    op.drop_index('idx_pwi_temp_code', table_name='project_work_items')
    op.drop_index('idx_pwi_master', table_name='project_work_items')
    op.drop_index('idx_pwi_resolution', table_name='project_work_items')
    op.drop_index('idx_pwi_gate_status', table_name='project_work_items')
    op.drop_index('idx_pwi_file', table_name='project_work_items')
    op.drop_index('idx_pwi_project', table_name='project_work_items')
    op.drop_table('project_work_items')

    # Drop enums (MySQL ignores these but good for PostgreSQL compatibility)
    sa.Enum(name='training_action_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='resolution_status_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='gate_status_enum').drop(op.get_bind(), checkfirst=True)
