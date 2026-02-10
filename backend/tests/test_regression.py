"""
Regression test suite for the Priority Processor.

Tests all 198 entries from test_data.json to ensure no regressions
when modifying normalization code.
"""
import json
import os
import pytest

from app.services.priority_processor import PriorityProcessor


# Load test data once
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'test_data.json')

with open(TEST_DATA_PATH, encoding='utf-8') as f:
    TEST_DATA = json.load(f)


@pytest.fixture(scope='module')
def processor():
    return PriorityProcessor()


class TestRegressionSuite:
    """Golden-file regression tests against test_data.json (198 cases)."""

    @pytest.mark.parametrize(
        "test_case",
        TEST_DATA,
        ids=[f"{i}_{t['category']}_{t['original'][:40]}" for i, t in enumerate(TEST_DATA)],
    )
    def test_normalization_matches_expected(self, processor, test_case):
        """Each test case should produce the expected normalized output."""
        result = processor.process(test_case['original'])
        assert result.normalized.strip().lower() == test_case['expected'].strip().lower(), (
            f"\nInput:    {test_case['original']}"
            f"\nExpected: {test_case['expected']}"
            f"\nGot:      {result.normalized}"
            f"\nNote:     {test_case.get('note', '')}"
        )


class TestRegressionStats:
    """Aggregate regression statistics."""

    def test_total_count(self):
        """Should have exactly 198 test cases."""
        assert len(TEST_DATA) == 198

    def test_all_pass(self, processor):
        """All 198 test cases should pass (aggregate check)."""
        mismatches = []
        for t in TEST_DATA:
            result = processor.process(t['original'])
            if result.normalized.strip().lower() != t['expected'].strip().lower():
                mismatches.append({
                    'original': t['original'],
                    'expected': t['expected'],
                    'got': result.normalized,
                })

        assert len(mismatches) == 0, (
            f"{len(mismatches)}/198 REGRESSIONS DETECTED:\n"
            + "\n".join(
                f"  [{m['original']}] expected [{m['expected']}] got [{m['got']}]"
                for m in mismatches[:10]
            )
            + ("\n  ..." if len(mismatches) > 10 else "")
        )

    def test_confidence_distribution(self, processor):
        """Check confidence distribution across all test cases."""
        high = medium = low = 0
        for t in TEST_DATA:
            result = processor.process(t['original'])
            if result.confidence > 0.8:
                high += 1
            elif result.confidence >= 0.5:
                medium += 1
            else:
                low += 1

        total = len(TEST_DATA)
        # Just record the distribution, don't fail
        print(f"\nConfidence distribution ({total} items):")
        print(f"  HIGH   (>0.8): {high} ({high/total*100:.1f}%)")
        print(f"  MEDIUM (0.5-0.8): {medium} ({medium/total*100:.1f}%)")
        print(f"  LOW    (<0.5): {low} ({low/total*100:.1f}%)")


class TestConfigValidation:
    """Test that all ObjectConfigs are valid at startup."""

    def test_validate_configs(self):
        """All ObjectConfig entries should pass validation."""
        from app.services.dictionaries.master_resource import validate_configs
        assert validate_configs() is True

    def test_all_transforms_registered(self):
        """All transforms referenced in configs should exist."""
        from app.services.dictionaries.master_resource import MASTER_RESOURCE_DICTIONARY
        from app.services.dictionaries.transforms import TRANSFORMS

        missing = []
        for obj_name, config in MASTER_RESOURCE_DICTIONARY.items():
            for part_name in ('part1', 'part2', 'part3'):
                mapping = getattr(config, part_name)
                if mapping.source == "computed" and mapping.transform:
                    if mapping.transform not in TRANSFORMS:
                        missing.append(f"{obj_name}.{part_name}: {mapping.transform}")

        assert len(missing) == 0, f"Missing transforms: {missing}"

    def test_all_extractors_valid(self):
        """All extractor references should be known classes."""
        from app.services.dictionaries.master_resource import (
            MASTER_RESOURCE_DICTIONARY, VALID_EXTRACTORS,
        )

        invalid = []
        for obj_name, config in MASTER_RESOURCE_DICTIONARY.items():
            if config.extractor and config.extractor not in VALID_EXTRACTORS:
                invalid.append(f"{obj_name}: {config.extractor}")

        assert len(invalid) == 0, f"Invalid extractors: {invalid}"
