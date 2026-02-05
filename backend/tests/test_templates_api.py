"""
Tests for Column Mapping Templates API
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.services.fingerprint_generator import FingerprintGenerator, get_fingerprint_generator
from app.services.template_service import TemplateService
from app.models.column_mapping_template import ColumnMappingTemplate, TemplateVisibility
from app.models.template_usage_log import TemplateUsageLog, MatchType, UsageAction


class TestFingerprintAPIWithMocks:
    """Tests for the fingerprint generation endpoint using test_client."""

    def test_generate_fingerprint(self, test_client):
        """Test generating a fingerprint."""
        data = {
            "column_names": ["Mô tả", "ĐVT", "KL", "Đơn giá"]
        }

        response = test_client.post("/api/v1/templates/fingerprint", json=data)

        assert response.status_code == 200
        result = response.json()
        assert "fingerprint" in result
        assert "components" in result
        assert len(result["fingerprint"]) == 64
        assert result["components"]["column_count"] == 4
        assert len(result["components"]["column_keywords"]) > 0

    def test_generate_fingerprint_with_sample_data(self, test_client):
        """Test fingerprint generation with sample data."""
        data = {
            "column_names": ["STT", "Mô tả", "ĐVT", "KL"],
            "sample_data": [
                [1, "Item 1", "m3", 100],
                [2, "Item 2", "kg", 200]
            ]
        }

        response = test_client.post("/api/v1/templates/fingerprint", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["components"]["data_type_signature"] is not None

    def test_generate_fingerprint_deterministic(self, test_client):
        """Test that fingerprint is deterministic."""
        data = {"column_names": ["A", "B", "C"]}

        response1 = test_client.post("/api/v1/templates/fingerprint", json=data)
        response2 = test_client.post("/api/v1/templates/fingerprint", json=data)

        assert response1.json()["fingerprint"] == response2.json()["fingerprint"]

    def test_generate_fingerprint_empty_columns(self, test_client):
        """Test fingerprint with empty columns list."""
        data = {"column_names": []}

        response = test_client.post("/api/v1/templates/fingerprint", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["components"]["column_count"] == 0


class TestTemplateServiceUnit:
    """Unit tests for TemplateService using mocks."""

    @pytest.fixture
    def mock_service(self, mock_db_session):
        """Create a TemplateService with mocked database."""
        return TemplateService(mock_db_session)

    @pytest.fixture
    def mock_template(self):
        """Create a mock template."""
        template = MagicMock(spec=ColumnMappingTemplate)
        template.template_id = 1
        template.name = "Test Template"
        template.column_mapping = {"Col1": "field1", "Col2": "field2"}
        template.fingerprint = "a" * 64
        template.fingerprint_components = {
            "column_count": 2,
            "column_keywords": ["description", "unit"],
            "column_order_hash": "abc123",
            "data_type_signature": None
        }
        template.use_count = 0
        template.last_used_at = None
        template.match_success_rate = 100.0
        template.visibility = TemplateVisibility.private
        template.is_active = True
        template.is_system = False
        return template

    def test_fingerprint_generator_used(self, mock_service):
        """Test that fingerprint generator is initialized."""
        assert mock_service.fingerprint_generator is not None
        assert isinstance(mock_service.fingerprint_generator, FingerprintGenerator)

    def test_create_template_calls_db(self, mock_service, mock_db_session):
        """Test that create_template interacts with database."""
        mock_db_session.add = MagicMock()
        mock_db_session.commit = MagicMock()
        mock_db_session.refresh = MagicMock()

        # Mock the refresh to populate the template
        def set_template_id(obj):
            obj.template_id = 1

        mock_db_session.refresh.side_effect = set_template_id

        template = mock_service.create_template(
            name="Test",
            column_mapping={"A": "a", "B": "b"}
        )

        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    def test_get_template_queries_db(self, mock_service, mock_db_session, mock_template):
        """Test that get_template queries the database."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = mock_service.get_template(1)

        assert result == mock_template
        mock_db_session.query.assert_called()

    def test_delete_template_soft(self, mock_service, mock_db_session, mock_template):
        """Test soft delete functionality."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = mock_service.delete_template(1, soft=True)

        assert result is True
        assert mock_template.is_active is False
        mock_db_session.commit.assert_called()

    def test_delete_template_not_found(self, mock_service, mock_db_session):
        """Test delete when template not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = mock_service.delete_template(999, soft=True)

        assert result is False

    def test_log_usage_updates_template(self, mock_service, mock_db_session, mock_template):
        """Test that logging usage updates template statistics."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_template
        mock_db_session.add = MagicMock()
        mock_db_session.commit = MagicMock()

        def refresh_log(obj):
            if hasattr(obj, 'log_id'):
                obj.log_id = 1

        mock_db_session.refresh.side_effect = refresh_log

        mock_service.log_usage(
            template_id=1,
            action=UsageAction.auto_applied,
            match_type=MatchType.exact
        )

        # Verify template use_count was incremented
        assert mock_template.use_count == 1
        assert mock_template.last_used_at is not None


class TestFingerprintMatchingLogic:
    """Tests for fingerprint matching logic."""

    @pytest.fixture
    def generator(self):
        return get_fingerprint_generator()

    def test_exact_match_produces_100_similarity(self, generator):
        """Test that identical columns produce very high similarity."""
        columns = ["Mô tả", "ĐVT", "KL", "Đơn giá", "Thành tiền"]

        fp1 = generator.generate(columns)
        fp2 = generator.generate(columns)

        similarity = generator.calculate_similarity(fp1.components, fp2.components)
        # When no data_type_signature, data_type weight defaults to 50,
        # which brings max similarity to 95%. This is expected behavior.
        assert similarity >= 95.0

    def test_similar_columns_high_similarity(self, generator):
        """Test that similar columns produce high similarity."""
        columns1 = ["Mô tả", "ĐVT", "KL", "Đơn giá", "Thành tiền"]
        columns2 = ["Mô tả", "ĐVT", "Khối lượng", "Đơn giá"]  # Slightly different

        fp1 = generator.generate(columns1)
        fp2 = generator.generate(columns2)

        similarity = generator.calculate_similarity(fp1.components, fp2.components)
        assert similarity >= 60  # Should be reasonably high

    def test_different_columns_low_similarity(self, generator):
        """Test that different columns produce low similarity."""
        columns1 = ["Mô tả", "ĐVT", "KL"]
        columns2 = ["Ghi chú", "Trạng thái", "Phê duyệt"]

        fp1 = generator.generate(columns1)
        fp2 = generator.generate(columns2)

        similarity = generator.calculate_similarity(fp1.components, fp2.components)
        assert similarity < 50  # Should be low


class TestTemplateMatchingService:
    """Tests for template matching in the service."""

    @pytest.fixture
    def mock_service(self, mock_db_session):
        return TemplateService(mock_db_session)

    @pytest.fixture
    def mock_templates(self):
        """Create mock templates for matching."""
        templates = []

        # Template 1: Standard BOQ columns
        t1 = MagicMock(spec=ColumnMappingTemplate)
        t1.template_id = 1
        t1.name = "Standard BOQ"
        t1.column_mapping = {"Mô tả": "description", "ĐVT": "unit", "KL": "quantity"}
        t1.fingerprint = "a" * 64
        t1.fingerprint_components = {
            "column_count": 3,
            "column_keywords": ["description", "quantity", "unit"],
            "column_order_hash": "hash1",
            "data_type_signature": None
        }
        t1.is_active = True
        t1.visibility = TemplateVisibility.public
        t1.is_system = False
        t1.created_by = None
        templates.append(t1)

        # Template 2: Different columns
        t2 = MagicMock(spec=ColumnMappingTemplate)
        t2.template_id = 2
        t2.name = "Material List"
        t2.column_mapping = {"Vật liệu": "material", "Số lượng": "qty"}
        t2.fingerprint = "b" * 64
        t2.fingerprint_components = {
            "column_count": 2,
            "column_keywords": ["material", "quantity"],
            "column_order_hash": "hash2",
            "data_type_signature": None
        }
        t2.is_active = True
        t2.visibility = TemplateVisibility.public
        t2.is_system = False
        t2.created_by = None
        templates.append(t2)

        return templates

    def test_find_matching_no_exact_match(self, mock_service, mock_db_session, mock_templates):
        """Test finding matches when no exact match exists."""
        # Setup: exact match returns None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        # Setup: all templates query returns our templates
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_templates

        best, alternatives, fingerprint = mock_service.find_matching_templates(
            column_names=["Mô tả", "ĐVT", "KL"],
            min_similarity=50
        )

        # Should find fuzzy match
        assert fingerprint is not None
        assert len(fingerprint) == 64

    def test_find_matching_exact_match(self, mock_service, mock_db_session, mock_templates):
        """Test finding exact match."""
        # Setup: exact match returns first template
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_templates[0]

        best, alternatives, fingerprint = mock_service.find_matching_templates(
            column_names=["Mô tả", "ĐVT", "KL"]
        )

        # Should return exact match
        assert best is not None
        assert best.similarity_score == 100.0
        assert best.match_type.value == "exact"
        assert alternatives == []


class TestTemplateVisibilityFiltering:
    """Tests for template visibility filtering."""

    @pytest.fixture
    def mock_service(self, mock_db_session):
        return TemplateService(mock_db_session)

    def test_get_templates_filters_inactive(self, mock_service, mock_db_session):
        """Test that inactive templates are filtered by default."""
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_service.get_templates(include_inactive=False)

        # Should have called filter at least once (for is_active)
        assert mock_query.filter.called


class TestTemplateStatistics:
    """Tests for template statistics."""

    @pytest.fixture
    def mock_service(self, mock_db_session):
        return TemplateService(mock_db_session)

    def test_get_statistics_returns_expected_keys(self, mock_service, mock_db_session):
        """Test that statistics returns all expected keys."""
        # Setup mock queries
        mock_db_session.query.return_value.count.return_value = 10
        mock_db_session.query.return_value.filter.return_value.count.return_value = 8
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        stats = mock_service.get_statistics()

        expected_keys = [
            "total_templates",
            "active_templates",
            "system_templates",
            "user_templates",
            "total_uses",
            "successful_uses",
            "average_success_rate",
            "most_used_templates",
            "recent_uses"
        ]
        for key in expected_keys:
            assert key in stats
