"""
Tests for SECCodeV4Mapper service.
"""
import pytest
from app.services.sec_code_v4_mapper import SECCodeV4Mapper, LEGACY_TO_V4_DISCIPLINE


class TestLegacyToV4Mapping:
    """Test legacy SEC → v4.0 discipline mapping."""

    def test_all_legacy_codes_mapped(self):
        """Every legacy SEC code should have a v4 discipline mapping."""
        expected = {
            'SEC-00': 'PM',
            'SEC-01': 'CV',
            'SEC-02': 'CV',
            'SEC-03': 'AR',
            'SEC-04': 'EL',
            'SEC-04-01': 'EL',
            'SEC-04-02': 'PL',
            'SEC-04-03': 'ME',
            'SEC-04-04': 'FP',
            'SEC-05': 'EX',
        }
        for sec_code, discipline in expected.items():
            assert LEGACY_TO_V4_DISCIPLINE[sec_code] == discipline, \
                f"{sec_code} should map to {discipline}"

    def test_mapper_discipline_method(self):
        """Test the mapper service method."""
        from unittest.mock import MagicMock
        db = MagicMock()
        mapper = SECCodeV4Mapper(db)

        assert mapper.legacy_to_discipline('SEC-01') == 'CV'
        assert mapper.legacy_to_discipline('SEC-03') == 'AR'
        assert mapper.legacy_to_discipline('SEC-04-01') == 'EL'
        assert mapper.legacy_to_discipline('SEC-04-02') == 'PL'
        assert mapper.legacy_to_discipline('SEC-04-03') == 'ME'
        assert mapper.legacy_to_discipline('SEC-04-04') == 'FP'
        assert mapper.legacy_to_discipline('SEC-05-03') == 'LA'

    def test_prefix_fallback(self):
        """Unknown sub-codes should fall back to parent prefix."""
        from unittest.mock import MagicMock
        db = MagicMock()
        mapper = SECCodeV4Mapper(db)

        # SEC-01-99 doesn't exist, should fall back to SEC-01 → CV
        assert mapper.legacy_to_discipline('SEC-01-99') == 'CV'

    def test_unknown_code_defaults_to_cv(self):
        """Completely unknown codes should default to CV."""
        from unittest.mock import MagicMock
        db = MagicMock()
        mapper = SECCodeV4Mapper(db)

        assert mapper.legacy_to_discipline('SEC-99') == 'CV'

    def test_get_full_mapping(self):
        """Full mapping should contain all entries."""
        from unittest.mock import MagicMock
        db = MagicMock()
        mapper = SECCodeV4Mapper(db)

        mapping = mapper.get_full_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 10
        assert 'SEC-01' in mapping
        assert 'SEC-04-02' in mapping


class TestDisciplineCoverage:
    """Test that all disciplines are reachable."""

    def test_all_disciplines_reachable(self):
        """All defined v4 disciplines should be reachable from some SEC code."""
        all_disciplines = set(LEGACY_TO_V4_DISCIPLINE.values())

        expected_disciplines = {'PM', 'CV', 'AR', 'EL', 'PL', 'ME', 'FP', 'EX', 'LA'}
        assert expected_disciplines.issubset(all_disciplines), \
            f"Missing disciplines: {expected_disciplines - all_disciplines}"

    def test_mep_sub_disciplines_distinct(self):
        """MEP sub-categories should map to distinct disciplines."""
        assert LEGACY_TO_V4_DISCIPLINE['SEC-04-01'] == 'EL'
        assert LEGACY_TO_V4_DISCIPLINE['SEC-04-02'] == 'PL'
        assert LEGACY_TO_V4_DISCIPLINE['SEC-04-03'] == 'ME'
        assert LEGACY_TO_V4_DISCIPLINE['SEC-04-04'] == 'FP'

        # All four should be different
        mep_disciplines = {
            LEGACY_TO_V4_DISCIPLINE[f'SEC-04-0{i}'] for i in range(1, 5)
        }
        assert len(mep_disciplines) == 4
