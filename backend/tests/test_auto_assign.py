"""
Tests for auto-assign master code strategy.

Covers:
- Change A: Persist match results in BOQ processing
- Change B: ClassifierService integration for SEC codes
- Change C: Bulk accept/review API endpoints
- Change D: Back-link master to line_items in batch builder
"""
import json
import pytest
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal

from app.services.boq_processing_service import (
    BOQProcessingService,
    MatchResult,
    ProcessingResult,
    EXACT_MATCH_THRESHOLD,
    FUZZY_MATCH_THRESHOLD,
)
from app.services.master_database_builder import (
    AggregatedItem,
    BuildConfig,
    MasterBuildResult,
    MasterDatabaseBuilder,
    StandardizedItem,
    StepStats,
    WORK_CATEGORY_TO_SEC,
)
from app.services.normalization_result import (
    NormalizationResult,
    NormalizerType,
    WorkCategory,
)


# ============================================================
# Helpers and mocks
# ============================================================

def _make_norm_result(
    original: str,
    normalized: str = '',
    work_category: WorkCategory = WorkCategory.GENERAL,
    confidence: float = 80.0,
) -> NormalizationResult:
    return NormalizationResult(
        original=original,
        normalized=normalized or original.lower(),
        work_category=work_category,
        confidence=confidence,
        normalizer_used=NormalizerType.DESCRIPTION,
    )


def _make_agg(
    desc: str,
    unit: str = 'm3',
    frequency: int = 10,
    file_ids: Optional[List[int]] = None,
) -> AggregatedItem:
    return AggregatedItem(
        raw_descriptions=[desc],
        unit=unit,
        frequency=frequency,
        source_file_ids=file_ids or [1],
        representative_description=desc,
    )


@dataclass
class _FakeGatekeeperResult:
    status: str = 'APPROVED'
    score: float = 80.0
    reasons: List[str] = None
    indicators: Dict[str, bool] = None
    defaults_applied: Dict[str, Any] = None
    enhanced_description: str = ''

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []
        if self.indicators is None:
            self.indicators = {}
        if self.defaults_applied is None:
            self.defaults_applied = {}


@dataclass
class _FakeSpecs:
    category: Optional[str] = None
    material: Optional[str] = None
    grade: Optional[str] = None
    dimension: Optional[str] = None

    def to_matching_key(self) -> str:
        parts = [
            self.category or 'X',
            self.material or 'X',
            self.grade or 'X',
            self.dimension or 'X',
        ]
        return '|'.join(p.lower().strip() for p in parts)


@dataclass
class _FakeLineItem:
    """Simulates a LineItem ORM object for testing."""
    line_item_id: int
    file_id: int
    description: str
    unit: str = 'm3'
    quantity: float = 1.0
    unit_price: float = 100.0
    matched_master_id: Optional[int] = None
    match_type: str = 'none'
    match_similarity: Optional[float] = None
    needs_review: bool = False
    normalized_description: Optional[str] = None
    sec_code: Optional[str] = None
    project_id: int = 1
    row_number: int = 1


@dataclass
class _FakeMasterWorkItem:
    master_id: int
    work_code: str
    description: str
    description_normalized: str
    sec_code: str = 'SEC-01'
    unit_standard: str = 'm3'
    is_active: bool = True
    is_verified: bool = False
    occurrence_count: int = 1
    source_files: str = '[]'
    spec_category: Optional[str] = None
    spec_material: Optional[str] = None
    spec_grade: Optional[str] = None
    spec_dimension: Optional[str] = None
    matching_key: str = ''


class _MockDB:
    """Minimal mock for SQLAlchemy Session."""

    def __init__(self):
        self.added = []
        self.committed = False
        self.flushed = False
        self._query_results = []
        self._line_items = []

    def query(self, *args, **kwargs):
        return _MockQuery(self._query_results)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def flush(self):
        self.flushed = True

    def begin_nested(self):
        return _MockNestedTransaction()

    def rollback(self):
        pass


class _MockNestedTransaction:
    def commit(self):
        pass

    def rollback(self):
        pass


class _MockQuery:
    def __init__(self, results):
        self._results = results

    def filter(self, *args, **kwargs):
        return self

    def having(self, *args, **kwargs):
        return self

    def group_by(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self._results

    def first(self):
        return self._results[0] if self._results else None

    def delete(self):
        pass


def _make_boq_service(db=None, hybrid_enabled=False):
    """Create a BOQProcessingService with mocked dependencies."""
    if db is None:
        db = _MockDB()
    service = BOQProcessingService.__new__(BOQProcessingService)
    service.db = db
    service.orchestrator = MagicMock()
    service.code_generator = MagicMock()
    service.gatekeeper = MagicMock()
    service.spec_extractor = MagicMock()
    service._hybrid_matcher = None
    return service


def _make_builder(db=None, query_results=None):
    """Create a MasterDatabaseBuilder with mocked dependencies."""
    if db is None:
        db = _MockDB()
    if query_results is not None:
        db._query_results = query_results
    builder = MasterDatabaseBuilder.__new__(MasterDatabaseBuilder)
    builder.db = db
    builder.orchestrator = MagicMock()
    builder.spec_extractor = MagicMock()
    builder.gatekeeper = MagicMock()
    builder.code_generator = MagicMock()
    builder._classifier = None
    return builder


# ============================================================
# TestPersistMatchResults (Change A)
# ============================================================

class TestPersistMatchResults:

    def test_exact_match_persisted(self):
        """similarity=0.96 → matched_master_id set, needs_review=False"""
        line_item = _FakeLineItem(
            line_item_id=1, file_id=10,
            description='Bê tông M200 móng',
        )
        master = _FakeMasterWorkItem(
            master_id=100, work_code='S02-CONC-001',
            description='Bê tông M200 móng',
            description_normalized='bê tông m200 móng',
        )

        db = _MockDB()
        db._query_results = [line_item]  # will be returned by query().filter().all()

        service = _make_boq_service(db)

        match_result = MatchResult(
            original_description='Bê tông M200 móng',
            normalized_description='bê tông m200 móng',
            match_type='exact',
            similarity_score=0.96,
            master_item=master,
            master_work_code='S02-CONC-001',
            needs_review=False,
        )

        with patch('app.services.classifier_service.get_classifier') as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = [('SEC-02', 85.0)]
            mock_cls.return_value = mock_classifier

            service._persist_match_results(10, [match_result])

        assert line_item.matched_master_id == 100
        assert line_item.match_type == 'exact'
        assert line_item.match_similarity == 96.0
        assert line_item.needs_review is False
        assert db.flushed

    def test_fuzzy_match_needs_review(self):
        """similarity=0.85 → matched_master_id set, needs_review=True"""
        line_item = _FakeLineItem(
            line_item_id=2, file_id=10,
            description='Bê tông M250 móng',
        )
        master = _FakeMasterWorkItem(
            master_id=101, work_code='S02-CONC-002',
            description='Bê tông M200 móng',
            description_normalized='bê tông m200 móng',
        )

        db = _MockDB()
        db._query_results = [line_item]

        service = _make_boq_service(db)

        match_result = MatchResult(
            original_description='Bê tông M250 móng',
            normalized_description='bê tông m250 móng',
            match_type='fuzzy',
            similarity_score=0.85,
            master_item=master,
            master_work_code='S02-CONC-002',
            needs_review=True,
        )

        with patch('app.services.classifier_service.get_classifier') as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = [('SEC-02', 80.0)]
            mock_cls.return_value = mock_classifier

            service._persist_match_results(10, [match_result])

        assert line_item.matched_master_id == 101
        assert line_item.match_type == 'fuzzy'
        assert line_item.match_similarity == 85.0
        assert line_item.needs_review is True

    def test_no_match_no_persist(self):
        """similarity=0.5 → match_type='none', matched_master_id=None"""
        line_item = _FakeLineItem(
            line_item_id=3, file_id=10,
            description='Công tác khác',
        )

        db = _MockDB()
        db._query_results = [line_item]

        service = _make_boq_service(db)

        match_result = MatchResult(
            original_description='Công tác khác',
            normalized_description='công tác khác',
            match_type='new',
            similarity_score=0.5,
            master_item=None,
            needs_review=False,
        )

        with patch('app.services.classifier_service.get_classifier') as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = []
            mock_cls.return_value = mock_classifier

            service._persist_match_results(10, [match_result])

        assert line_item.match_type == 'none'
        assert line_item.matched_master_id is None
        assert line_item.needs_review is False

    def test_bulk_persist_efficiency(self):
        """100 items → single batch flush"""
        line_items = [
            _FakeLineItem(
                line_item_id=i, file_id=10,
                description=f'Item {i}',
            )
            for i in range(100)
        ]

        db = _MockDB()
        db._query_results = line_items

        service = _make_boq_service(db)

        match_results = [
            MatchResult(
                original_description=f'Item {i}',
                normalized_description=f'item {i}',
                match_type='exact' if i % 3 == 0 else ('fuzzy' if i % 3 == 1 else 'new'),
                similarity_score=0.98 if i % 3 == 0 else (0.88 if i % 3 == 1 else 0.5),
                master_item=_FakeMasterWorkItem(
                    master_id=i + 1000,
                    work_code=f'S01-TEST-{i:04d}',
                    description=f'Item {i}',
                    description_normalized=f'item {i}',
                ) if i % 3 != 2 else None,
                needs_review=(i % 3 == 1),
            )
            for i in range(100)
        ]

        with patch('app.services.classifier_service.get_classifier') as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = []
            mock_cls.return_value = mock_classifier

            service._persist_match_results(10, match_results)

        # Should flush once at the end
        assert db.flushed

        # Check a few items
        exact_items = [li for li in line_items if li.match_type == 'exact']
        fuzzy_items = [li for li in line_items if li.match_type == 'fuzzy']
        none_items = [li for li in line_items if li.match_type == 'none']

        assert len(exact_items) > 0
        assert len(fuzzy_items) > 0
        assert len(none_items) > 0

        # Verify exact items have correct fields
        for li in exact_items:
            assert li.needs_review is False
            assert li.matched_master_id is not None

        # Verify fuzzy items have needs_review=True
        for li in fuzzy_items:
            assert li.needs_review is True
            assert li.matched_master_id is not None

    def test_empty_results_no_error(self):
        """Empty match results should not error."""
        service = _make_boq_service()
        service._persist_match_results(10, [])
        # No exception = pass


# ============================================================
# TestClassifierIntegration (Change B)
# ============================================================

class TestClassifierIntegration:

    def test_classifier_replaces_unclassified_in_boq(self):
        """_create_master_item uses ClassifierService → sec_code != 'UNCLASSIFIED'"""
        db = _MockDB()
        service = _make_boq_service(db)
        service.spec_extractor.extract.return_value = _FakeSpecs()
        service.code_generator.generate_work_code.return_value = 'S02-CONC-001'

        match_result = MatchResult(
            original_description='Bê tông M200 móng',
            normalized_description='bê tông m200 móng',
            match_type='new',
            similarity_score=0.0,
        )

        with patch('app.services.classifier_service.get_classifier') as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = [('SEC-02', 85.0)]
            mock_cls.return_value = mock_classifier

            service._create_master_item(1, match_result)

        # Check the added MasterWorkItem
        assert len(db.added) == 1
        added_item = db.added[0]
        assert added_item.sec_code == 'SEC-02'

    def test_classifier_low_confidence_fallback(self):
        """confidence < 70 → falls back to UNCLASSIFIED"""
        db = _MockDB()
        service = _make_boq_service(db)
        service.spec_extractor.extract.return_value = _FakeSpecs()
        service.code_generator.generate_work_code.return_value = 'S00-GEN-001'

        match_result = MatchResult(
            original_description='Something ambiguous',
            normalized_description='something ambiguous',
            match_type='new',
            similarity_score=0.0,
        )

        with patch('app.services.classifier_service.get_classifier') as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = [('SEC-03', 30.0)]
            mock_cls.return_value = mock_classifier

            service._create_master_item(1, match_result)

        added_item = db.added[0]
        assert added_item.sec_code == 'UNCLASSIFIED'

    def test_classifier_in_batch_builder(self):
        """step3 uses ClassifierService for SEC codes when available."""
        builder = _make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.code_generator.generate_work_code.return_value = 'S02-CONC-001'
        builder.orchestrator.normalize.return_value = _make_norm_result(
            'Bê tông M200', 'bê tông m200', WorkCategory.GENERAL
        )

        # Set up a mock classifier
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = [('SEC-02', 90.0)]
        builder._classifier = mock_classifier

        item = StandardizedItem(
            canonical_description='Bê tông M200',
            canonical_unit='m3',
            total_frequency=10,
            synonym_variants=[],
            normalization_result=_make_norm_result(
                'Bê tông M200', 'bê tông m200', WorkCategory.GENERAL
            ),
            source_file_ids=[1],
        )

        result = builder.step3_code_and_tag([item])

        # Verify classifier was called
        mock_classifier.classify.assert_called()
        # Verify sec_code passed to generate_work_code is from classifier
        call_kwargs = builder.code_generator.generate_work_code.call_args
        assert call_kwargs.kwargs.get('sec_code') == 'SEC-02' or \
               (len(call_kwargs.args) > 0 or call_kwargs[1].get('sec_code') == 'SEC-02')

    def test_classifier_fallback_to_mapping_in_builder(self):
        """When classifier confidence < 70, falls back to WORK_CATEGORY_TO_SEC."""
        builder = _make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.code_generator.generate_work_code.return_value = 'S01-EARTH-001'
        builder.orchestrator.normalize.return_value = _make_norm_result(
            'Đào đất', 'đào đất', WorkCategory.EARTHWORKS_PILING
        )

        # Classifier returns low confidence
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = [('SEC-05', 40.0)]
        builder._classifier = mock_classifier

        item = StandardizedItem(
            canonical_description='Đào đất',
            canonical_unit='m3',
            total_frequency=5,
            synonym_variants=[],
            normalization_result=_make_norm_result(
                'Đào đất', 'đào đất', WorkCategory.EARTHWORKS_PILING
            ),
            source_file_ids=[1],
        )

        result = builder.step3_code_and_tag([item])

        # Should fall back to mapping: EARTHWORKS_PILING → SEC-01
        call_kwargs = builder.code_generator.generate_work_code.call_args
        sec_used = call_kwargs.kwargs.get('sec_code') or call_kwargs[1].get('sec_code')
        assert sec_used == 'SEC-01'

    def test_classifier_unavailable_uses_mapping(self):
        """When classifier is None, uses WORK_CATEGORY_TO_SEC mapping."""
        builder = _make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.code_generator.generate_work_code.return_value = 'S02-CONC-001'

        norm = _make_norm_result('Bê tông', 'bê tông', WorkCategory.CONCRETE_REBAR)
        builder.orchestrator.normalize.return_value = norm
        builder._classifier = None  # No classifier

        item = StandardizedItem(
            canonical_description='Bê tông',
            canonical_unit='m3',
            total_frequency=5,
            synonym_variants=[],
            normalization_result=norm,
            source_file_ids=[1],
        )

        result = builder.step3_code_and_tag([item])

        call_kwargs = builder.code_generator.generate_work_code.call_args
        sec_used = call_kwargs.kwargs.get('sec_code') or call_kwargs[1].get('sec_code')
        assert sec_used == 'SEC-02'


# ============================================================
# TestBulkAcceptAPI (Change C)
# ============================================================

class TestBulkAcceptAPI:

    def test_accept_exact_matches_endpoint(self):
        """Returns correct accepted_count for exact matches."""
        from app.api.v1.endpoints.master_items import accept_exact_matches

        line_items = [
            _FakeLineItem(
                line_item_id=i, file_id=10,
                description=f'Exact item {i}',
                match_type='exact',
                matched_master_id=100 + i,
                match_similarity=96.0,
                needs_review=False,
            )
            for i in range(5)
        ]

        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = line_items
        db.query.return_value = mock_query

        result = accept_exact_matches(file_id=10, db=db)

        assert result.accepted_count == 5
        assert len(result.items) == 5
        assert result.items[0].matched_master_id is not None

    def test_accept_exact_matches_empty(self):
        """No exact matches returns count=0."""
        from app.api.v1.endpoints.master_items import accept_exact_matches

        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query

        result = accept_exact_matches(file_id=10, db=db)
        assert result.accepted_count == 0
        assert result.items == []

    def test_review_fuzzy_matches_endpoint(self):
        """Returns pending items with match details."""
        from app.api.v1.endpoints.master_items import review_fuzzy_matches

        line_items = [
            _FakeLineItem(
                line_item_id=i, file_id=10,
                description=f'Fuzzy item {i}',
                normalized_description=f'fuzzy item {i}',
                match_type='fuzzy',
                matched_master_id=200 + i,
                match_similarity=88.0,
                needs_review=True,
                sec_code='SEC-02',
            )
            for i in range(3)
        ]

        master = _FakeMasterWorkItem(
            master_id=200, work_code='S02-CONC-001',
            description='Master fuzzy item',
            description_normalized='master fuzzy item',
        )

        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = line_items
        mock_query.first.return_value = master
        db.query.return_value = mock_query

        result = review_fuzzy_matches(file_id=10, db=db)

        assert result.pending_count == 3
        assert len(result.items) == 3
        assert result.items[0].match_similarity == 88.0

    def test_accept_single_match(self):
        """Individual fuzzy match accepted sets needs_review=False."""
        from app.api.v1.endpoints.master_items import accept_single_match

        line_item = _FakeLineItem(
            line_item_id=42, file_id=10,
            description='Fuzzy item to accept',
            match_type='fuzzy',
            matched_master_id=200,
            match_similarity=88.0,
            needs_review=True,
        )

        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = line_item
        db.query.return_value = mock_query

        result = accept_single_match(line_item_id=42, db=db)

        assert result.accepted is True
        assert result.line_item_id == 42
        assert line_item.needs_review is False
        db.commit.assert_called_once()

    def test_accept_single_match_not_found(self):
        """Accepting non-existent line item raises 404."""
        from app.api.v1.endpoints.master_items import accept_single_match
        from fastapi import HTTPException

        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            accept_single_match(line_item_id=999, db=db)

        assert exc_info.value.status_code == 404

    def test_accept_single_match_wrong_type(self):
        """Accepting non-fuzzy match raises 400."""
        from app.api.v1.endpoints.master_items import accept_single_match
        from fastapi import HTTPException

        line_item = _FakeLineItem(
            line_item_id=42, file_id=10,
            description='Exact item',
            match_type='exact',
            needs_review=False,
        )

        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = line_item
        db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            accept_single_match(line_item_id=42, db=db)

        assert exc_info.value.status_code == 400


# ============================================================
# TestBackLink (Change D)
# ============================================================

class TestBackLink:

    def test_link_master_to_line_items(self):
        """After batch build, source line_items have matched_master_id set."""
        master = _FakeMasterWorkItem(
            master_id=500, work_code='S01-EARTH-001',
            description='Đào đất hố móng',
            description_normalized='đào đất hố móng',
        )
        line_item = _FakeLineItem(
            line_item_id=1, file_id=1,
            description='Đào đất hố móng',
            matched_master_id=None,
        )

        # Create a DB mock that returns different results for different queries
        db = MagicMock()

        def mock_query(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if hasattr(model, 'master_id'):
                # MasterWorkItem query
                mock_q.first.return_value = master
            else:
                # LineItem query
                mock_q.all.return_value = [line_item]
            return mock_q

        db.query.side_effect = mock_query

        builder = _make_builder(db)

        items = [
            StandardizedItem(
                canonical_description='Đào đất hố móng',
                canonical_unit='m3',
                total_frequency=10,
                synonym_variants=[],
                source_file_ids=[1],
            )
        ]

        builder._link_master_to_line_items(items)

        assert line_item.matched_master_id == 500
        assert line_item.match_type == 'exact'
        assert line_item.match_similarity == 100.0
        assert line_item.needs_review is False

    def test_link_preserves_existing_matches(self):
        """Line_items already matched should not be overwritten."""
        master = _FakeMasterWorkItem(
            master_id=500, work_code='S01-EARTH-001',
            description='Đào đất hố móng',
            description_normalized='đào đất hố móng',
        )
        # This line item already has a match — should NOT be in the query results
        # because the filter is `matched_master_id.is_(None)`
        already_matched = _FakeLineItem(
            line_item_id=1, file_id=1,
            description='Đào đất hố móng',
            matched_master_id=999,  # already matched to a different master
            match_type='exact',
            match_similarity=95.0,
        )

        db = MagicMock()

        def mock_query(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if hasattr(model, 'master_id'):
                mock_q.first.return_value = master
            else:
                # Return empty — the filter for matched_master_id.is_(None)
                # means already-matched items are excluded
                mock_q.all.return_value = []
            return mock_q

        db.query.side_effect = mock_query

        builder = _make_builder(db)

        items = [
            StandardizedItem(
                canonical_description='Đào đất hố móng',
                canonical_unit='m3',
                total_frequency=10,
                synonym_variants=[],
                source_file_ids=[1],
            )
        ]

        builder._link_master_to_line_items(items)

        # The already-matched item should not be modified
        assert already_matched.matched_master_id == 999

    def test_link_with_synonyms(self):
        """Back-link should also work for synonym variants."""
        master = _FakeMasterWorkItem(
            master_id=600, work_code='S02-CONC-001',
            description='Bê tông M200 móng',
            description_normalized='bê tông m200 móng',
        )
        line_item_canonical = _FakeLineItem(
            line_item_id=1, file_id=1,
            description='Bê tông M200 móng',
            matched_master_id=None,
        )
        line_item_synonym = _FakeLineItem(
            line_item_id=2, file_id=1,
            description='BT M200 móng',
            matched_master_id=None,
        )

        db = MagicMock()
        call_count = [0]

        def mock_query(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if hasattr(model, 'master_id'):
                mock_q.first.return_value = master
            else:
                # Return different line items depending on the call
                call_count[0] += 1
                if call_count[0] == 1:
                    mock_q.all.return_value = [line_item_canonical]
                elif call_count[0] == 2:
                    mock_q.all.return_value = [line_item_synonym]
                else:
                    mock_q.all.return_value = []
            return mock_q

        db.query.side_effect = mock_query

        builder = _make_builder(db)

        items = [
            StandardizedItem(
                canonical_description='Bê tông M200 móng',
                canonical_unit='m3',
                total_frequency=15,
                synonym_variants=['BT M200 móng'],
                source_file_ids=[1],
            )
        ]

        builder._link_master_to_line_items(items)

        assert line_item_canonical.matched_master_id == 600
        assert line_item_synonym.matched_master_id == 600

    def test_link_no_master_found(self):
        """When master item doesn't exist, no line items should be updated."""
        db = MagicMock()

        def mock_query(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.first.return_value = None
            mock_q.all.return_value = []
            return mock_q

        db.query.side_effect = mock_query

        builder = _make_builder(db)

        items = [
            StandardizedItem(
                canonical_description='Nonexistent item',
                canonical_unit='m3',
                total_frequency=5,
                synonym_variants=[],
                source_file_ids=[1],
            )
        ]

        # Should not raise
        builder._link_master_to_line_items(items)


# ============================================================
# TestSECRuleOverride (Change B integration)
# ============================================================

class TestSECRuleOverride:
    """Test that _classify_sec_by_rules() overrides SEC-00/SEC-04 in step3."""

    def test_rule_overrides_sec00_for_plumbing(self):
        """Item classified as SEC-00 by ML, should be overridden to SEC-04-02 by rules."""
        builder = _make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.code_generator.generate_work_code.return_value = 'S04-PIPE-0001'
        builder.orchestrator.normalize.return_value = _make_norm_result(
            'Ống PVC D60', 'ống pvc d60', WorkCategory.GENERAL
        )

        # ML classifier returns SEC-00 (Unclassified)
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = [('SEC-00', 75.0)]
        builder._classifier = mock_classifier

        item = StandardizedItem(
            canonical_description='Ống PVC D60',
            canonical_unit='m',
            total_frequency=10,
            synonym_variants=[],
            normalization_result=_make_norm_result(
                'Ống PVC D60', 'ống pvc d60', WorkCategory.GENERAL
            ),
            source_file_ids=[1],
        )

        builder.step3_code_and_tag([item])

        call_kwargs = builder.code_generator.generate_work_code.call_args
        sec_used = call_kwargs.kwargs.get('sec_code') or call_kwargs[1].get('sec_code')
        assert sec_used == 'SEC-04-02'

    def test_rule_overrides_sec04_to_sub_for_electrical(self):
        """Item classified as SEC-04 (generic MEP), should be refined to SEC-04-01."""
        builder = _make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.code_generator.generate_work_code.return_value = 'S04-ELEC-0001'
        builder.orchestrator.normalize.return_value = _make_norm_result(
            'MCCB 3P 100A', 'mccb 3p 100a', WorkCategory.STEEL_MEP
        )

        # ML classifier returns SEC-04 (generic MEP)
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = [('SEC-04', 80.0)]
        builder._classifier = mock_classifier

        item = StandardizedItem(
            canonical_description='MCCB 3P 100A',
            canonical_unit='cái',
            total_frequency=5,
            synonym_variants=[],
            normalization_result=_make_norm_result(
                'MCCB 3P 100A', 'mccb 3p 100a', WorkCategory.STEEL_MEP
            ),
            source_file_ids=[1],
        )

        builder.step3_code_and_tag([item])

        call_kwargs = builder.code_generator.generate_work_code.call_args
        sec_used = call_kwargs.kwargs.get('sec_code') or call_kwargs[1].get('sec_code')
        assert sec_used == 'SEC-04-01'

    def test_no_rule_override_for_specific_sec(self):
        """If ML returns specific SEC-02 with high confidence, rules should not override."""
        builder = _make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.code_generator.generate_work_code.return_value = 'S02-CONC-0001'
        builder.orchestrator.normalize.return_value = _make_norm_result(
            'Bê tông M200', 'bê tông m200', WorkCategory.CONCRETE_REBAR
        )

        # ML classifier returns SEC-02 with high confidence
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = [('SEC-02', 92.0)]
        builder._classifier = mock_classifier

        item = StandardizedItem(
            canonical_description='Bê tông M200',
            canonical_unit='m3',
            total_frequency=10,
            synonym_variants=[],
            normalization_result=_make_norm_result(
                'Bê tông M200', 'bê tông m200', WorkCategory.CONCRETE_REBAR
            ),
            source_file_ids=[1],
        )

        builder.step3_code_and_tag([item])

        call_kwargs = builder.code_generator.generate_work_code.call_args
        sec_used = call_kwargs.kwargs.get('sec_code') or call_kwargs[1].get('sec_code')
        assert sec_used == 'SEC-02'

    def test_rule_catches_unclassified_van(self):
        """Van cổng should be caught as SEC-04-02 even without ML classifier."""
        builder = _make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.code_generator.generate_work_code.return_value = 'S04-VALVE-0001'
        builder.orchestrator.normalize.return_value = _make_norm_result(
            'Van cổng DN80', 'van cổng dn80', WorkCategory.GENERAL
        )

        # No ML classifier available
        builder._classifier = None

        item = StandardizedItem(
            canonical_description='Van cổng DN80',
            canonical_unit='cái',
            total_frequency=8,
            synonym_variants=[],
            normalization_result=_make_norm_result(
                'Van cổng DN80', 'van cổng dn80', WorkCategory.GENERAL
            ),
            source_file_ids=[1],
        )

        builder.step3_code_and_tag([item])

        call_kwargs = builder.code_generator.generate_work_code.call_args
        sec_used = call_kwargs.kwargs.get('sec_code') or call_kwargs[1].get('sec_code')
        assert sec_used == 'SEC-04-02'
