# Import all models here for Alembic to detect them
from app.models.user import User
from app.models.project import Project
from app.models.boq_file import BOQFile
from app.models.line_item import LineItem
from app.models.sec_code import SECCode
from app.models.master_work_item import MasterWorkItem
from app.models.price_history import PriceHistory
from app.models.boq_version import BOQVersion
from app.models.line_item_flag import LineItemFlag
from app.models.pending_master_item import PendingMasterItem
from app.models.quarantine_log import QuarantineLog
from app.models.master_synonym import MasterSynonym
from app.models.unit_standard import UnitStandard, SecCodeDefaultUnit
from app.models.column_mapping_template import ColumnMappingTemplate, TemplateVisibility
from app.models.template_usage_log import TemplateUsageLog, MatchType, UsageAction
from app.models.spec_change_log import SpecChangeLog
from app.models.sec_code_v4 import SECCodeV4
from app.models.activity_bom import ActivityBOM
from app.models.project_work_item import ProjectWorkItem
from app.models.ai_training_log import AITrainingLog

__all__ = [
    "User",
    "Project",
    "BOQFile",
    "LineItem",
    "SECCode",
    "MasterWorkItem",
    "PriceHistory",
    "BOQVersion",
    "LineItemFlag",
    "PendingMasterItem",
    "QuarantineLog",
    "MasterSynonym",
    "UnitStandard",
    "SecCodeDefaultUnit",
    "ColumnMappingTemplate",
    "TemplateVisibility",
    "TemplateUsageLog",
    "MatchType",
    "UsageAction",
    "SpecChangeLog",
    "SECCodeV4",
    "ActivityBOM",
    "ProjectWorkItem",
    "AITrainingLog",
]
