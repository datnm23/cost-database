"""
Tests for MasterDatabaseBuilder — 3-Step Pipeline

Covers:
- Step 1: Aggregation (frequency counting, dedup, multi-file)
- Step 2: Standardization (normalization, clustering, canonical election, Pareto)
- Step 3: Coding & Tagging (code generation, SEC, gatekeeper, persistence)
- End-to-end: Full 3-step pipeline with mock data
"""
import json
import pytest
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock

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
# Fixtures & helpers
# ============================================================

def _make_norm_result(
    original: str,
    normalized: str = '',
    work_category: WorkCategory = WorkCategory.GENERAL,
    confidence: float = 80.0,
) -> NormalizationResult:
    """Helper to build a NormalizationResult."""
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


class _MockDB:
    """Minimal mock for SQLAlchemy Session used in builder tests."""

    def __init__(self):
        self.added = []
        self.committed = False
        self.flushed = False
        self._query_results = []

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


# ============================================================
# Test Step 1: Aggregation
# ============================================================

class TestStep1Aggregation:

    def _make_builder(self, query_results=None):
        db = _MockDB()
        if query_results is not None:
            db._query_results = query_results
        builder = MasterDatabaseBuilder.__new__(MasterDatabaseBuilder)
        builder.db = db
        builder.orchestrator = MagicMock()
        builder.spec_extractor = MagicMock()
        builder.gatekeeper = MagicMock()
        builder.code_generator = MagicMock()
        return builder

    def test_empty_file_ids(self):
        builder = self._make_builder()
        result = builder.step1_aggregate([])
        assert result == []

    def test_aggregation_returns_sorted_by_frequency(self):
        """Verify items come back sorted by frequency descending."""
        # Simulate SQL rows
        Row = type('Row', (), {})

        row1 = Row()
        row1.description = 'Đào đất hố móng'
        row1.unit = 'm3'
        row1.file_count = 3
        row1.total_count = 50
        row1.file_ids_str = '1,2,3'

        row2 = Row()
        row2.description = 'Bê tông M200 móng'
        row2.unit = 'm3'
        row2.file_count = 2
        row2.total_count = 30
        row2.file_ids_str = '1,2'

        row3 = Row()
        row3.description = 'Xây tường gạch'
        row3.unit = 'm2'
        row3.file_count = 1
        row3.total_count = 10
        row3.file_ids_str = '1'

        builder = self._make_builder([row1, row2, row3])
        result = builder.step1_aggregate([1, 2, 3])

        assert len(result) == 3
        assert result[0].frequency == 50
        assert result[1].frequency == 30
        assert result[2].frequency == 10
        assert result[0].representative_description == 'Đào đất hố móng'

    def test_source_file_ids_parsed_correctly(self):
        Row = type('Row', (), {})
        row = Row()
        row.description = 'Test item'
        row.unit = 'm'
        row.file_count = 3
        row.total_count = 5
        row.file_ids_str = '10,20,30'

        builder = self._make_builder([row])
        result = builder.step1_aggregate([10, 20, 30])

        assert result[0].source_file_ids == [10, 20, 30]

    def test_parse_file_ids_handles_none(self):
        builder = self._make_builder()
        assert builder._parse_file_ids(None) == []
        assert builder._parse_file_ids('') == []

    def test_parse_file_ids_handles_single(self):
        builder = self._make_builder()
        assert builder._parse_file_ids('42') == [42]


# ============================================================
# Test Step 2: Standardization
# ============================================================

class TestStep2Standardization:

    def _make_builder(self):
        db = _MockDB()
        builder = MasterDatabaseBuilder.__new__(MasterDatabaseBuilder)
        builder.db = db
        builder.orchestrator = MagicMock()
        builder.spec_extractor = MagicMock()
        builder.gatekeeper = MagicMock()
        builder.code_generator = MagicMock()
        return builder

    def test_empty_input(self):
        builder = self._make_builder()
        result = builder.step2_standardize([])
        assert result == []

    def test_single_item_becomes_single_cluster(self):
        builder = self._make_builder()
        agg = _make_agg('Đào đất hố móng', frequency=10)
        norm = _make_norm_result('Đào đất hố móng', 'đào đất hố móng')
        builder.orchestrator.normalize_batch.return_value = [norm]

        result = builder.step2_standardize([agg])

        assert len(result) == 1
        assert result[0].canonical_description == 'Đào đất hố móng'
        assert result[0].total_frequency == 10
        assert result[0].is_pareto_top is True
        assert result[0].synonym_variants == []

    def test_identical_descriptions_cluster_together(self):
        builder = self._make_builder()
        agg1 = _make_agg('Bê tông M200', frequency=20, file_ids=[1])
        agg2 = _make_agg('Bê tông M200', frequency=15, file_ids=[2])

        norm1 = _make_norm_result('Bê tông M200', 'bê tông m200')
        norm2 = _make_norm_result('Bê tông M200', 'bê tông m200')
        builder.orchestrator.normalize_batch.return_value = [norm1, norm2]

        result = builder.step2_standardize([agg1, agg2], clustering_threshold=0.85)

        # Should cluster into 1 item with combined frequency
        assert len(result) == 1
        assert result[0].total_frequency == 35

    def test_different_units_not_clustered(self):
        builder = self._make_builder()
        agg1 = _make_agg('Bê tông M200', unit='m3', frequency=20)
        agg2 = _make_agg('Bê tông M200', unit='m2', frequency=15)

        norm1 = _make_norm_result('Bê tông M200', 'bê tông m200')
        norm2 = _make_norm_result('Bê tông M200', 'bê tông m200')
        builder.orchestrator.normalize_batch.return_value = [norm1, norm2]

        result = builder.step2_standardize([agg1, agg2])

        # Different units → separate clusters
        assert len(result) == 2

    def test_canonical_election_picks_highest_frequency(self):
        builder = self._make_builder()
        agg1 = _make_agg('Ống PVC D20', frequency=5, file_ids=[1])
        agg2 = _make_agg('Ống nhựa PVC D20', frequency=25, file_ids=[2])

        # After normalization, these should be similar enough to cluster
        norm1 = _make_norm_result('Ống PVC D20', 'ống pvc d20')
        norm2 = _make_norm_result('Ống nhựa PVC D20', 'ống nhựa pvc d20')
        builder.orchestrator.normalize_batch.return_value = [norm1, norm2]

        # These won't naturally cluster with SequenceMatcher at 0.85
        # because the strings differ. Let's use a lower threshold for this test.
        result = builder.step2_standardize([agg1, agg2], clustering_threshold=0.65)

        assert len(result) == 1
        # Highest frequency wins
        assert result[0].canonical_description == 'Ống nhựa PVC D20'
        assert result[0].total_frequency == 30

    def test_pareto_marks_top_items(self):
        builder = self._make_builder()

        items = [
            _make_agg(f'Item {i}', frequency=100 - i * 10)
            for i in range(10)
        ]
        norms = [
            _make_norm_result(f'Item {i}', f'item {i}')
            for i in range(10)
        ]
        builder.orchestrator.normalize_batch.return_value = norms

        result = builder.step2_standardize(items, pareto_threshold=0.80)

        # Items are sorted by frequency: 100, 90, 80, 70, 60, 50, 40, 30, 20, 10
        # Total = 550
        # 80% of 550 = 440
        # Cumulative: 100, 190, 270, 350, 410, 460 → need 6 items to reach 460 ≥ 440
        pareto_items = [s for s in result if s.is_pareto_top]
        non_pareto = [s for s in result if not s.is_pareto_top]

        assert len(pareto_items) >= 1
        assert len(non_pareto) >= 1
        # All items still present
        assert len(result) == 10

    def test_pareto_cumulative_logic(self):
        """Verify exact Pareto cutoff."""
        builder = self._make_builder()

        # 3 items: freq 80, 15, 5. Total=100. 80% threshold = 80.
        # First item alone reaches 80 → only 1 pareto item.
        items = [
            _make_agg('A', frequency=80),
            _make_agg('B', frequency=15, unit='kg'),
            _make_agg('C', frequency=5, unit='ton'),
        ]
        norms = [
            _make_norm_result('A', 'a'),
            _make_norm_result('B', 'b'),
            _make_norm_result('C', 'c'),
        ]
        builder.orchestrator.normalize_batch.return_value = norms

        result = builder.step2_standardize(items, pareto_threshold=0.80)

        pareto = [s for s in result if s.is_pareto_top]
        assert len(pareto) == 1
        assert pareto[0].total_frequency == 80

    def test_normalize_for_index(self):
        builder = self._make_builder()
        assert builder._normalize_for_index('  BÊ TÔNG  M200  ') == 'bê tông m200'
        assert builder._normalize_for_index('') == ''
        assert builder._normalize_for_index(None) == ''


# ============================================================
# Test Step 3: Coding & Tagging
# ============================================================

class TestStep3CodingTagging:

    def _make_builder(self):
        db = _MockDB()
        builder = MasterDatabaseBuilder.__new__(MasterDatabaseBuilder)
        builder.db = db
        builder.orchestrator = MagicMock()
        builder.spec_extractor = MagicMock()
        builder.gatekeeper = MagicMock()
        builder.code_generator = MagicMock()

        # Default mock returns
        builder.orchestrator.normalize.return_value = _make_norm_result(
            'test', 'test', WorkCategory.CONCRETE_REBAR
        )
        builder.spec_extractor.extract.return_value = _FakeSpecs(
            category='be tong', grade='M200'
        )
        builder.code_generator.generate_work_code.return_value = 'S02-CONC-M200-0001'

        return builder

    def test_approved_item_added_to_master(self):
        builder = self._make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )

        item = StandardizedItem(
            canonical_description='Bê tông M200 móng',
            canonical_unit='m3',
            total_frequency=10,
            synonym_variants=[],
            normalization_result=_make_norm_result(
                'Bê tông M200 móng', 'bê tông m200 móng',
                WorkCategory.CONCRETE_REBAR
            ),
            source_file_ids=[1, 2],
        )

        result = builder.step3_code_and_tag([item])

        assert result.total_master_added == 1
        assert result.total_pending == 0
        assert result.total_quarantined == 0
        assert builder.db.committed

    def test_pending_item_goes_to_staging(self):
        builder = self._make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='PENDING_REVIEW', score=60.0, reasons=['Low specs']
        )

        item = StandardizedItem(
            canonical_description='Something vague',
            canonical_unit='m',
            total_frequency=5,
            synonym_variants=[],
            source_file_ids=[1],
        )

        result = builder.step3_code_and_tag([item])

        assert result.total_master_added == 0
        assert result.total_pending == 1

    def test_rejected_item_quarantined(self):
        builder = self._make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='REJECTED', score=30.0, reasons=['Forbidden pattern: header text']
        )

        item = StandardizedItem(
            canonical_description='Header row text',
            canonical_unit=None,
            total_frequency=2,
            synonym_variants=[],
            source_file_ids=[1],
        )

        result = builder.step3_code_and_tag([item])

        assert result.total_master_added == 0
        assert result.total_quarantined == 1

    def test_auto_approve_promotes_pending_to_master(self):
        builder = self._make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='PENDING_REVIEW', score=65.0
        )

        config = BuildConfig(auto_approve=True)
        item = StandardizedItem(
            canonical_description='Moderate quality item',
            canonical_unit='m2',
            total_frequency=8,
            synonym_variants=[],
            source_file_ids=[1],
        )

        result = builder.step3_code_and_tag([item], config)

        assert result.total_master_added == 1
        assert result.total_pending == 0

    def test_synonyms_persisted(self):
        builder = self._make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=90.0
        )

        item = StandardizedItem(
            canonical_description='Ống HDPE D110',
            canonical_unit='m',
            total_frequency=20,
            synonym_variants=['Ống nhựa HDPE D110', 'Ống PE D110'],
            source_file_ids=[1, 2],
        )

        result = builder.step3_code_and_tag([item])

        assert result.total_synonyms_added == 2

    def test_sec_code_derived_from_work_category(self):
        """Verify SEC code is derived from NormalizationResult.work_category."""
        builder = self._make_builder()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )

        for category, expected_sec in WORK_CATEGORY_TO_SEC.items():
            norm = _make_norm_result('test', 'test', category)
            item = StandardizedItem(
                canonical_description='test',
                canonical_unit='m',
                total_frequency=1,
                synonym_variants=[],
                normalization_result=norm,
                source_file_ids=[1],
            )
            builder.step3_code_and_tag([item])

            # Check that generate_work_code was called with correct sec_code
            call_kwargs = builder.code_generator.generate_work_code.call_args
            assert call_kwargs[1]['sec_code'] == expected_sec or \
                   call_kwargs.kwargs.get('sec_code') == expected_sec

    def test_error_handling_continues_processing(self):
        """If one item fails, others should still be processed."""
        builder = self._make_builder()
        call_count = 0

        def side_effect(item, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Simulated error")
            return _FakeGatekeeperResult(status='APPROVED', score=85.0)

        builder.gatekeeper.validate.side_effect = side_effect

        items = [
            StandardizedItem(
                canonical_description=f'Item {i}',
                canonical_unit='m',
                total_frequency=i + 1,
                synonym_variants=[],
                source_file_ids=[1],
            )
            for i in range(3)
        ]

        result = builder.step3_code_and_tag(items)

        # First item failed, 2 should succeed
        assert result.total_master_added == 2


# ============================================================
# Test End-to-End
# ============================================================

class TestEndToEnd:

    def _make_builder(self, query_results=None):
        db = _MockDB()
        if query_results is not None:
            db._query_results = query_results
        builder = MasterDatabaseBuilder.__new__(MasterDatabaseBuilder)
        builder.db = db
        builder.orchestrator = MagicMock()
        builder.spec_extractor = MagicMock()
        builder.gatekeeper = MagicMock()
        builder.code_generator = MagicMock()
        return builder

    def test_full_pipeline_empty_input(self):
        builder = self._make_builder([])
        result = builder.build(file_ids=[])
        assert result.total_master_added == 0
        assert result.step1_stats.output_count == 0

    def test_full_pipeline_with_data(self):
        """Full pipeline: aggregate → standardize → code & tag."""
        builder = self._make_builder()  # empty query results for step3

        # Mock step1 to return aggregated items directly
        aggregated = [
            _make_agg('Đào đất hố móng', unit='m3', frequency=50, file_ids=[1, 2]),
            _make_agg('Bê tông M200 móng', unit='m3', frequency=30, file_ids=[1, 2]),
            _make_agg('Xây tường gạch', unit='m2', frequency=10, file_ids=[1, 2]),
        ]
        builder.step1_aggregate = MagicMock(return_value=aggregated)

        # Mock normalize_batch to return proper results
        builder.orchestrator.normalize_batch.return_value = [
            _make_norm_result('Đào đất hố móng', 'đào đất hố móng', WorkCategory.EARTHWORKS_PILING),
            _make_norm_result('Bê tông M200 móng', 'bê tông m200 móng', WorkCategory.CONCRETE_REBAR),
            _make_norm_result('Xây tường gạch', 'xây tường gạch', WorkCategory.FINISHING),
        ]
        builder.orchestrator.normalize.return_value = _make_norm_result(
            'test', 'test', WorkCategory.GENERAL
        )

        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.code_generator.generate_work_code.return_value = 'S01-EARTH-0001'

        config = BuildConfig(pareto_threshold=0.80, min_frequency=1)
        result = builder.build(file_ids=[1, 2], config=config)

        # Step 1: 3 unique descriptions
        assert result.step1_stats.output_count == 3
        assert result.step1_stats.input_count == 2  # 2 file_ids

        # Step 2: 3 clusters (all different descriptions)
        assert result.step2_stats.output_count == 3

        # Step 3: All approved
        assert result.total_master_added == 3
        assert result.total_pending == 0
        assert result.total_quarantined == 0

    def test_progress_callback_called(self):
        builder = self._make_builder([])
        callbacks = []

        def on_progress(step, current, total):
            callbacks.append((step, current, total))

        builder.build(file_ids=[], progress_callback=on_progress)

        # At minimum, should call aggregation and done
        assert ('aggregation', 0, 3) in callbacks

    def test_include_only_pareto(self):
        """When include_only_pareto=True, step 3 only processes Pareto items."""
        builder = self._make_builder()  # empty query results for step3

        # Mock step1 to return aggregated items
        aggregated = [
            _make_agg('High freq item', unit='m3', frequency=90, file_ids=[1]),
            _make_agg('Low freq item', unit='m2', frequency=10, file_ids=[1]),
        ]
        builder.step1_aggregate = MagicMock(return_value=aggregated)

        builder.orchestrator.normalize_batch.return_value = [
            _make_norm_result('High freq item', 'high freq item'),
            _make_norm_result('Low freq item', 'low freq item'),
        ]
        builder.orchestrator.normalize.return_value = _make_norm_result('test', 'test')
        builder.spec_extractor.extract.return_value = _FakeSpecs()
        builder.gatekeeper.validate.return_value = _FakeGatekeeperResult(
            status='APPROVED', score=85.0
        )
        builder.code_generator.generate_work_code.return_value = 'S00-GEN-0001'

        config = BuildConfig(
            pareto_threshold=0.80,
            include_only_pareto=True,
        )
        result = builder.build(file_ids=[1], config=config)

        # Only 1 item should be processed in step 3 (the Pareto one)
        assert result.step3_stats.input_count == 1
        assert result.total_master_added == 1

    def test_clear_existing(self):
        """clear_existing should call delete on all tables before building."""
        builder = self._make_builder([])
        config = BuildConfig(clear_existing=True)

        # Track delete calls
        delete_calls = []
        original_query = builder.db.query

        class TrackingQuery(_MockQuery):
            def delete(self_q):
                delete_calls.append(True)

        def mock_query(*args, **kwargs):
            return TrackingQuery([])

        builder.db.query = mock_query

        builder.build(file_ids=[], config=config)

        # Should have called delete for: MasterSynonym, PendingMasterItem, QuarantineLog, MasterWorkItem
        assert len(delete_calls) == 4


# ============================================================
# Test internal helpers
# ============================================================

class TestInternalHelpers:

    def _make_builder(self):
        db = _MockDB()
        builder = MasterDatabaseBuilder.__new__(MasterDatabaseBuilder)
        builder.db = db
        builder.orchestrator = MagicMock()
        builder.spec_extractor = MagicMock()
        builder.gatekeeper = MagicMock()
        builder.code_generator = MagicMock()
        return builder

    def test_cluster_descriptions_same_unit_cluster(self):
        builder = self._make_builder()
        agg1 = _make_agg('Bê tông M200 móng', unit='m3', frequency=10)
        agg2 = _make_agg('Bê tông M200 móng', unit='m3', frequency=5)

        norm1 = _make_norm_result('Bê tông M200 móng', 'bê tông m200 móng')
        norm2 = _make_norm_result('Bê tông M200 móng', 'bê tông m200 móng')

        items = [(agg1, norm1), (agg2, norm2)]
        clusters = builder._cluster_descriptions(items, threshold=0.85)

        assert len(clusters) == 1
        assert len(clusters[0]) == 2

    def test_cluster_descriptions_diff_unit_separate(self):
        builder = self._make_builder()
        agg1 = _make_agg('Bê tông M200', unit='m3', frequency=10)
        agg2 = _make_agg('Bê tông M200', unit='m2', frequency=5)

        norm1 = _make_norm_result('Bê tông M200', 'bê tông m200')
        norm2 = _make_norm_result('Bê tông M200', 'bê tông m200')

        items = [(agg1, norm1), (agg2, norm2)]
        clusters = builder._cluster_descriptions(items, threshold=0.85)

        assert len(clusters) == 2

    def test_elect_canonical_highest_frequency(self):
        builder = self._make_builder()

        agg_low = _make_agg('Short', frequency=5, file_ids=[1])
        norm_low = _make_norm_result('Short', 'short')
        agg_high = _make_agg('Higher frequency item', frequency=20, file_ids=[2])
        norm_high = _make_norm_result('Higher frequency item', 'higher frequency item')

        cluster = [(agg_low, norm_low), (agg_high, norm_high)]
        result = builder._elect_canonical(cluster, cluster_id=0)

        assert result.canonical_description == 'Higher frequency item'
        assert result.total_frequency == 25
        assert 'Short' in result.synonym_variants

    def test_elect_canonical_tiebreak_by_length(self):
        builder = self._make_builder()

        agg1 = _make_agg('A short', frequency=10, file_ids=[1])
        norm1 = _make_norm_result('A short', 'a short')
        agg2 = _make_agg('A much longer description', frequency=10, file_ids=[2])
        norm2 = _make_norm_result('A much longer description', 'a much longer description')

        cluster = [(agg1, norm1), (agg2, norm2)]
        result = builder._elect_canonical(cluster, cluster_id=0)

        # Same frequency, longer wins
        assert result.canonical_description == 'A much longer description'

    def test_apply_pareto_all_items_when_needed(self):
        builder = self._make_builder()

        # All items needed to reach threshold
        items = [
            StandardizedItem(
                canonical_description=f'Item {i}',
                canonical_unit='m',
                total_frequency=10,
                synonym_variants=[],
            )
            for i in range(5)
        ]
        # Total = 50, 80% = 40, need 4 items to reach 40
        builder._apply_pareto(items, 0.80)

        pareto = [i for i in items if i.is_pareto_top]
        assert len(pareto) == 4

    def test_apply_pareto_zero_total(self):
        builder = self._make_builder()
        items = [
            StandardizedItem(
                canonical_description='Empty',
                canonical_unit='m',
                total_frequency=0,
                synonym_variants=[],
            )
        ]
        builder._apply_pareto(items, 0.80)
        # No items should be marked (total is 0)
        assert not items[0].is_pareto_top
