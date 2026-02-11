"""
Tests for SpecLifecycleService.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.spec_lifecycle_service import SpecLifecycleService, SOURCE_CONFIDENCE


class FakeMasterItem:
    """Minimal fake for MasterWorkItem."""
    def __init__(self, **kwargs):
        self.master_id = kwargs.get('master_id', 1)
        self.spec_category = kwargs.get('spec_category', None)
        self.spec_material = kwargs.get('spec_material', None)
        self.spec_grade = kwargs.get('spec_grade', None)
        self.spec_dimension = kwargs.get('spec_dimension', None)
        self.spec_status = kwargs.get('spec_status', 'draft')
        self.spec_source = kwargs.get('spec_source', 'default')
        self.spec_confidence = kwargs.get('spec_confidence', 0.3)
        self.spec_completeness = kwargs.get('spec_completeness', 0.0)
        self.is_verified = kwargs.get('is_verified', False)

    def compute_spec_completeness(self):
        score = 0.0
        if self.spec_category:
            score += 0.25
        if self.spec_material:
            score += 0.25
        if self.spec_grade:
            score += 0.30
        if self.spec_dimension:
            score += 0.20
        return round(score, 2)


class TestSpecCompleteness:
    """Test completeness scoring."""

    def test_empty_specs_zero(self):
        item = FakeMasterItem()
        assert item.compute_spec_completeness() == 0.0

    def test_all_specs_full(self):
        item = FakeMasterItem(
            spec_category='be tong',
            spec_material='xi mang',
            spec_grade='M300',
            spec_dimension='600x600',
        )
        assert item.compute_spec_completeness() == 1.0

    def test_only_category(self):
        item = FakeMasterItem(spec_category='be tong')
        assert item.compute_spec_completeness() == 0.25

    def test_category_and_grade(self):
        item = FakeMasterItem(spec_category='be tong', spec_grade='M300')
        assert item.compute_spec_completeness() == 0.55

    def test_all_except_dimension(self):
        item = FakeMasterItem(
            spec_category='be tong',
            spec_material='xi mang',
            spec_grade='M300',
        )
        assert item.compute_spec_completeness() == 0.80

    def test_grade_has_highest_weight(self):
        """Grade weight (0.30) > category (0.25) = material (0.25) > dimension (0.20)."""
        grade_only = FakeMasterItem(spec_grade='M300')
        cat_only = FakeMasterItem(spec_category='be tong')
        dim_only = FakeMasterItem(spec_dimension='600x600')

        assert grade_only.compute_spec_completeness() > cat_only.compute_spec_completeness()
        assert cat_only.compute_spec_completeness() > dim_only.compute_spec_completeness()


class TestSpecPromotion:
    """Test status promotion validation."""

    def test_cannot_promote_to_lower(self):
        """Cannot go from detailed → draft."""
        db = MagicMock()
        item = FakeMasterItem(spec_status='detailed', spec_completeness=0.8)
        db.query.return_value.filter.return_value.first.return_value = item

        service = SpecLifecycleService(db)
        with pytest.raises(ValueError, match="target must be higher"):
            service.promote_status(1, 'draft')

    def test_cannot_promote_same_status(self):
        """Cannot promote to same status."""
        db = MagicMock()
        item = FakeMasterItem(spec_status='draft', spec_completeness=0.8)
        db.query.return_value.filter.return_value.first.return_value = item

        service = SpecLifecycleService(db)
        with pytest.raises(ValueError, match="target must be higher"):
            service.promote_status(1, 'draft')

    def test_promote_draft_to_detailed_requires_50pct(self):
        """draft → detailed requires completeness >= 50%."""
        db = MagicMock()
        item = FakeMasterItem(spec_status='draft', spec_completeness=0.30)
        db.query.return_value.filter.return_value.first.return_value = item

        service = SpecLifecycleService(db)
        with pytest.raises(ValueError, match="50%"):
            service.promote_status(1, 'detailed')

    def test_promote_draft_to_detailed_passes_at_50pct(self):
        """draft → detailed passes at exactly 50%."""
        db = MagicMock()
        item = FakeMasterItem(spec_status='draft', spec_completeness=0.50)
        db.query.return_value.filter.return_value.first.return_value = item

        service = SpecLifecycleService(db)
        result = service.promote_status(1, 'detailed')
        assert result.spec_status == 'detailed'

    def test_promote_to_final_requires_verified(self):
        """detailed → final requires is_verified=True."""
        db = MagicMock()
        item = FakeMasterItem(
            spec_status='detailed',
            spec_completeness=0.80,
            is_verified=False,
        )
        db.query.return_value.filter.return_value.first.return_value = item

        service = SpecLifecycleService(db)
        with pytest.raises(ValueError, match="verified"):
            service.promote_status(1, 'final')

    def test_promote_to_final_requires_75pct(self):
        """detailed → final requires completeness >= 75%."""
        db = MagicMock()
        item = FakeMasterItem(
            spec_status='detailed',
            spec_completeness=0.55,
            is_verified=True,
        )
        db.query.return_value.filter.return_value.first.return_value = item

        service = SpecLifecycleService(db)
        with pytest.raises(ValueError, match="75%"):
            service.promote_status(1, 'final')

    def test_promote_to_final_succeeds(self):
        """detailed → final succeeds with completeness >= 75% and verified."""
        db = MagicMock()
        item = FakeMasterItem(
            spec_status='detailed',
            spec_completeness=0.80,
            is_verified=True,
        )
        db.query.return_value.filter.return_value.first.return_value = item

        service = SpecLifecycleService(db)
        result = service.promote_status(1, 'final')
        assert result.spec_status == 'final'


class TestSourceConfidence:
    """Test confidence mapping by source."""

    def test_default_confidence(self):
        assert SOURCE_CONFIDENCE['default'] == 0.3

    def test_boq_confidence(self):
        assert SOURCE_CONFIDENCE['boq'] == 0.5

    def test_drawing_confidence(self):
        assert SOURCE_CONFIDENCE['drawing'] == 0.8

    def test_as_built_confidence(self):
        assert SOURCE_CONFIDENCE['as_built'] == 1.0

    def test_confidence_ordering(self):
        """Confidence increases with source reliability."""
        assert (
            SOURCE_CONFIDENCE['default']
            < SOURCE_CONFIDENCE['boq']
            < SOURCE_CONFIDENCE['drawing']
            < SOURCE_CONFIDENCE['as_built']
        )


class TestSpecUpdate:
    """Test spec field updates with audit trail."""

    def test_update_creates_log(self):
        """Updating a spec field should add a SpecChangeLog entry."""
        db = MagicMock()
        item = FakeMasterItem(spec_grade='M200')
        db.query.return_value.filter.return_value.first.return_value = item

        service = SpecLifecycleService(db)
        result = service.update_spec(
            master_id=1,
            field='spec_grade',
            value='M300',
            source='boq',
        )

        # Verify db.add was called (for the log entry)
        assert db.add.called
        assert result.spec_grade == 'M300'
        assert result.spec_source == 'boq'
        assert result.spec_confidence == 0.5

    def test_update_nonexistent_item_raises(self):
        """Updating a non-existent item should raise ValueError."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        service = SpecLifecycleService(db)
        with pytest.raises(ValueError, match="not found"):
            service.update_spec(1, 'spec_grade', 'M300')
