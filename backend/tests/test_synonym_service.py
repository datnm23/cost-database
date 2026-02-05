"""
Tests for Synonym Service.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestSynonymService:
    """Tests for SynonymService."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def synonym_service(self, mock_db_session):
        """Create a SynonymService instance."""
        from app.services.synonym_service import SynonymService
        return SynonymService(mock_db_session)

    @pytest.fixture
    def mock_synonym(self):
        """Create a mock synonym."""
        synonym = MagicMock()
        synonym.synonym_id = 1
        synonym.master_id = 100
        synonym.synonym_text = "BT lót móng"
        synonym.synonym_normalized = "bt lót móng"
        synonym.synonym_type = "abbreviation"
        synonym.is_active = True
        return synonym

    @pytest.fixture
    def mock_master_item(self):
        """Create a mock master item."""
        item = MagicMock()
        item.master_id = 100
        item.work_code = "BT-LOT-001"
        item.description = "Bê tông lót móng"
        item.description_normalized = "bê tông lót móng"
        return item

    def test_build_synonym_cache(self, synonym_service, mock_db_session, mock_synonym):
        """build_synonym_cache should populate cache."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_synonym
        ]

        count = synonym_service.build_synonym_cache()

        assert count == 1
        assert synonym_service._cache_built == True
        assert "bt lót móng" in synonym_service._synonym_cache
        assert synonym_service._synonym_cache["bt lót móng"] == 100

    def test_find_by_synonym_from_cache(self, synonym_service, mock_db_session, mock_synonym, mock_master_item):
        """find_by_synonym should return from cache if available."""
        # Pre-populate cache
        synonym_service._synonym_cache = {"bt lót móng": 100}
        synonym_service._cache_built = True

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_master_item

        result = synonym_service.find_by_synonym("BT lót móng")

        assert result is not None
        assert result.master_id == 100

    def test_find_by_synonym_from_db_fallback(self, synonym_service, mock_db_session, mock_synonym, mock_master_item):
        """find_by_synonym should fallback to DB if not in cache."""
        # Empty cache but marked as built
        synonym_service._synonym_cache = {}
        synonym_service._cache_built = True

        # Setup mock for DB query
        mock_synonym.master_item = mock_master_item
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_synonym

        result = synonym_service.find_by_synonym("new synonym")

        assert result == mock_master_item
        # Should be added to cache
        assert "new synonym" in synonym_service._synonym_cache

    def test_find_by_synonym_not_found(self, synonym_service, mock_db_session):
        """find_by_synonym should return None if not found."""
        synonym_service._synonym_cache = {}
        synonym_service._cache_built = True

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = synonym_service.find_by_synonym("nonexistent")

        assert result is None

    def test_add_synonym_success(self, synonym_service, mock_db_session):
        """add_synonym should create new synonym."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add = MagicMock()
        mock_db_session.commit = MagicMock()
        mock_db_session.refresh = MagicMock()

        synonym_service._synonym_cache = {}

        result = synonym_service.add_synonym(
            master_id=100,
            synonym_text="BT lót nền",
            synonym_type="abbreviation",
            added_by=1
        )

        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        # Cache should be updated
        assert "bt lót nền" in synonym_service._synonym_cache

    def test_add_synonym_duplicate_fails(self, synonym_service, mock_db_session, mock_synonym):
        """add_synonym should fail for duplicates."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_synonym

        with pytest.raises(ValueError) as exc_info:
            synonym_service.add_synonym(
                master_id=200,
                synonym_text="BT lót móng",  # Already exists
                synonym_type="alias"
            )

        assert "already exists" in str(exc_info.value)

    def test_get_synonyms_for_master(self, synonym_service, mock_db_session, mock_synonym):
        """get_synonyms should return all synonyms for a master item."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_synonym
        ]

        result = synonym_service.get_synonyms(master_id=100)

        assert len(result) == 1
        assert result[0].synonym_id == 1

    def test_delete_synonym_success(self, synonym_service, mock_db_session, mock_synonym):
        """delete_synonym should soft-delete and remove from cache."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_synonym
        mock_db_session.commit = MagicMock()

        # Pre-populate cache
        synonym_service._synonym_cache = {"bt lót móng": 100}

        result = synonym_service.delete_synonym(synonym_id=1)

        assert result == True
        assert mock_synonym.is_active == False
        assert mock_db_session.commit.called
        assert "bt lót móng" not in synonym_service._synonym_cache

    def test_delete_synonym_not_found(self, synonym_service, mock_db_session):
        """delete_synonym should return False if not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = synonym_service.delete_synonym(synonym_id=999)

        assert result == False

    def test_get_statistics(self, synonym_service, mock_db_session):
        """get_statistics should return comprehensive stats."""
        mock_db_session.query.return_value.count.return_value = 50
        mock_db_session.query.return_value.filter.return_value.count.return_value = 45
        mock_db_session.query.return_value.group_by.return_value.all.return_value = [
            ("alias", 20),
            ("abbreviation", 15),
            ("regional", 10)
        ]

        synonym_service._synonym_cache = {"a": 1, "b": 2}

        result = synonym_service.get_statistics()

        assert result["total"] == 50
        assert result["active"] == 45
        assert result["inactive"] == 5
        assert result["cached"] == 2


class TestSynonymServiceCaseInsensitivity:
    """Test case-insensitivity in synonym service."""

    def test_find_by_synonym_case_insensitive(self):
        """find_by_synonym should be case-insensitive."""
        from app.services.synonym_service import SynonymService

        mock_db = MagicMock()
        service = SynonymService(mock_db)

        # Setup cache with lowercase
        service._synonym_cache = {"bê tông lót": 100}
        service._cache_built = True

        mock_item = MagicMock()
        mock_item.master_id = 100
        mock_db.query.return_value.filter.return_value.first.return_value = mock_item

        # Search with different cases
        result1 = service.find_by_synonym("Bê Tông Lót")
        result2 = service.find_by_synonym("BÊ TÔNG LÓT")
        result3 = service.find_by_synonym("bê tông lót")

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

    def test_add_synonym_normalizes_text(self):
        """add_synonym should normalize text to lowercase."""
        from app.services.synonym_service import SynonymService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = SynonymService(mock_db)
        service._synonym_cache = {}

        service.add_synonym(
            master_id=100,
            synonym_text="BT LÓT MÓNG",  # Uppercase
            synonym_type="abbreviation"
        )

        # Cache key should be lowercase
        assert "bt lót móng" in service._synonym_cache


class TestSynonymServiceIntegration:
    """Integration-style tests for synonym matching flow."""

    def test_synonym_lookup_workflow(self):
        """Test complete synonym lookup workflow."""
        from app.services.synonym_service import SynonymService

        mock_db = MagicMock()
        service = SynonymService(mock_db)

        # 1. Build cache
        mock_synonyms = [
            MagicMock(
                synonym_id=1,
                master_id=100,
                synonym_normalized="bt móng",
                is_active=True
            ),
            MagicMock(
                synonym_id=2,
                master_id=100,
                synonym_normalized="concrete footing",
                is_active=True
            ),
            MagicMock(
                synonym_id=3,
                master_id=200,
                synonym_normalized="vk gỗ",
                is_active=True
            ),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_synonyms

        count = service.build_synonym_cache()
        assert count == 3

        # 2. Look up Vietnamese abbreviation
        mock_master = MagicMock(master_id=100, description="Bê tông móng")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_master

        result = service.find_by_synonym("BT móng")
        assert result.master_id == 100

        # 3. Look up English synonym
        result = service.find_by_synonym("Concrete Footing")
        assert result.master_id == 100

        # 4. Non-existent synonym
        service._synonym_cache = {"bt móng": 100}  # Reset cache
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.find_by_synonym("unknown term")
        assert result is None
