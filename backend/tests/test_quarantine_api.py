"""
Tests for Quarantine API endpoints.
"""
import pytest
from unittest.mock import MagicMock


class TestQuarantineAPI:
    """Tests for quarantine API endpoints."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_quarantine_log(self):
        """Create a mock quarantine log."""
        log = MagicMock()
        log.log_id = 1
        log.description = "Invalid item XYZ"
        log.description_normalized = "invalid item xyz"
        log.source_file_id = 10
        log.rejection_reason = "forbidden_pattern"
        log.quality_score = 25.0
        log.matched_forbidden_pattern = "XYZ"
        log.quality_indicators = '{"has_verb": false, "has_material": false}'
        log.created_at = "2026-02-03T10:00:00"
        return log

    def test_list_quarantine_logs(self, mock_db_session, mock_quarantine_log):
        """GET /quarantine should return quarantine logs."""
        from app.api.v1.endpoints.quarantine import list_quarantine_logs

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_quarantine_log]
        mock_db_session.query.return_value = query_mock

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            list_quarantine_logs(
                rejection_reason=None,
                skip=0,
                limit=50,
                db=mock_db_session
            )
        )

        assert len(result) == 1
        assert result[0].log_id == 1
        assert result[0].rejection_reason == "forbidden_pattern"

    def test_list_quarantine_logs_with_filter(self, mock_db_session, mock_quarantine_log):
        """GET /quarantine should filter by rejection reason."""
        from app.api.v1.endpoints.quarantine import list_quarantine_logs

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_quarantine_log]
        mock_db_session.query.return_value = query_mock

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            list_quarantine_logs(
                rejection_reason="forbidden_pattern",
                skip=0,
                limit=50,
                db=mock_db_session
            )
        )

        # Filter should be called
        assert query_mock.filter.called
        assert len(result) == 1

    def test_get_quarantine_stats(self, mock_db_session):
        """GET /quarantine/stats should return statistics by reason."""
        from app.api.v1.endpoints.quarantine import get_quarantine_stats
        from sqlalchemy import func

        # Mock the group by query
        mock_result = [
            ("forbidden_pattern", 15),
            ("low_quality", 10),
            ("duplicate", 5),
        ]
        mock_db_session.query.return_value.group_by.return_value.all.return_value = mock_result

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            get_quarantine_stats(db=mock_db_session)
        )

        assert result.total == 30
        assert result.by_reason["forbidden_pattern"] == 15
        assert result.by_reason["low_quality"] == 10
        assert result.by_reason["duplicate"] == 5

    def test_get_quarantine_log_found(self, mock_db_session, mock_quarantine_log):
        """GET /quarantine/{id} should return log if exists."""
        from app.api.v1.endpoints.quarantine import get_quarantine_log

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_quarantine_log

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            get_quarantine_log(log_id=1, db=mock_db_session)
        )

        assert result.log_id == 1
        assert result.description == "Invalid item XYZ"

    def test_get_quarantine_log_not_found(self, mock_db_session):
        """GET /quarantine/{id} should return 404 if not exists."""
        from app.api.v1.endpoints.quarantine import get_quarantine_log
        from fastapi import HTTPException

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                get_quarantine_log(log_id=999, db=mock_db_session)
            )

        assert exc_info.value.status_code == 404

    def test_delete_quarantine_log(self, mock_db_session, mock_quarantine_log):
        """DELETE /quarantine/{id} should remove log."""
        from app.api.v1.endpoints.quarantine import delete_quarantine_log

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_quarantine_log
        mock_db_session.delete = MagicMock()
        mock_db_session.commit = MagicMock()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            delete_quarantine_log(log_id=1, db=mock_db_session)
        )

        assert result["status"] == "deleted"
        assert mock_db_session.delete.called
        assert mock_db_session.commit.called


class TestQuarantinePromoteToPending:
    """Tests for promote to pending feature."""

    def test_promote_to_pending_success(self):
        """POST /quarantine/{id}/promote-to-pending should create pending item."""
        from app.api.v1.endpoints.quarantine import promote_to_pending

        mock_db = MagicMock()
        mock_log = MagicMock()
        mock_log.log_id = 1
        mock_log.description = "Test description"
        mock_log.description_normalized = "test description"
        mock_log.source_file_id = 10
        mock_log.quality_score = 35.0
        mock_log.quality_indicators = '{"has_verb": false}'
        mock_log.rejection_reason = "low_quality"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_log
        mock_db.add = MagicMock()
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            promote_to_pending(log_id=1, db=mock_db)
        )

        assert result["status"] == "promoted"
        assert result["original_log_id"] == 1
        assert mock_db.add.called
        assert mock_db.delete.called

    def test_promote_not_found_raises_404(self):
        """POST /quarantine/{id}/promote-to-pending should return 404 if not found."""
        from app.api.v1.endpoints.quarantine import promote_to_pending
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                promote_to_pending(log_id=999, db=mock_db)
            )

        assert exc_info.value.status_code == 404


class TestQuarantineAnalytics:
    """Tests for quarantine analytics."""

    def test_get_rejection_reasons(self):
        """GET /quarantine/reasons/list should return unique reasons."""
        from app.api.v1.endpoints.quarantine import get_rejection_reasons

        mock_db = MagicMock()
        mock_db.query.return_value.distinct.return_value.all.return_value = [
            ("forbidden_pattern",),
            ("low_quality",),
            ("duplicate",),
            (None,),  # Should be filtered out
        ]

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            get_rejection_reasons(db=mock_db)
        )

        assert len(result) == 3
        assert "forbidden_pattern" in result
        assert "low_quality" in result
        assert "duplicate" in result
        assert None not in result

    def test_quarantine_logs_pagination(self):
        """Quarantine logs should support pagination."""
        from app.api.v1.endpoints.quarantine import list_quarantine_logs

        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock

        import asyncio

        # Test skip and limit
        asyncio.get_event_loop().run_until_complete(
            list_quarantine_logs(
                rejection_reason=None,
                source_file_id=None,
                skip=20,
                limit=10,
                db=mock_db
            )
        )

        query_mock.offset.assert_called_with(20)
        query_mock.limit.assert_called_with(10)
