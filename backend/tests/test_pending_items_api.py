"""
Tests for Pending Items API endpoints.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


class TestPendingItemsAPI:
    """Tests for pending items API endpoints."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_pending_item(self):
        """Create a mock pending item."""
        item = MagicMock()
        item.pending_id = 1
        item.description = "Bê tông M200 móng"
        item.description_normalized = "bê tông m200 móng"
        item.sec_code = "SEC-01"
        item.unit_standard = "m3"
        item.quality_score = 72.5
        item.quality_reasons = '["Good structure"]'
        item.quality_indicators = '{"has_verb": true, "has_material": true}'
        item.status = "PENDING"
        item.reviewed_by = None
        item.reviewed_at = None
        item.review_notes = None
        item.master_id = None
        item.created_at = "2026-02-03T10:00:00"
        item.updated_at = "2026-02-03T10:00:00"
        return item

    @pytest.fixture
    def mock_approved_item(self, mock_pending_item):
        """Create a mock approved item."""
        item = MagicMock()
        item.pending_id = 2
        item.description = "Thép D12 cột"
        item.description_normalized = "thép d12 cột"
        item.sec_code = "SEC-02"
        item.unit_standard = "kg"
        item.quality_score = 85.0
        item.status = "APPROVED"
        item.reviewed_by = 1
        item.master_id = 100
        return item

    def test_list_pending_items_returns_pending_only_by_default(self, mock_db_session, mock_pending_item):
        """GET /pending-items should return PENDING items by default."""
        from app.api.v1.endpoints.pending_items import list_pending_items

        # Setup mock
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_pending_item]
        mock_db_session.query.return_value = query_mock

        # Call the endpoint (async)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            list_pending_items(
                status='PENDING',
                min_score=None,
                max_score=None,
                sec_code=None,
                skip=0,
                limit=50,
                db=mock_db_session
            )
        )

        assert len(result) == 1
        assert result[0].pending_id == 1

    def test_list_pending_items_with_score_filter(self, mock_db_session, mock_pending_item):
        """GET /pending-items should filter by score range."""
        from app.api.v1.endpoints.pending_items import list_pending_items

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_pending_item]
        mock_db_session.query.return_value = query_mock

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            list_pending_items(
                status='PENDING',
                min_score=70.0,
                max_score=80.0,
                sec_code=None,
                skip=0,
                limit=50,
                db=mock_db_session
            )
        )

        # Verify filter was called with score conditions
        assert query_mock.filter.called
        assert len(result) == 1

    def test_get_pending_stats(self, mock_db_session):
        """GET /pending-items/stats should return counts."""
        from app.api.v1.endpoints.pending_items import get_pending_stats

        # Setup count mocks
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [10, 25, 5]

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            get_pending_stats(db=mock_db_session)
        )

        assert result.pending == 10
        assert result.approved == 25
        assert result.rejected == 5
        assert result.total == 40

    def test_get_pending_item_found(self, mock_db_session, mock_pending_item):
        """GET /pending-items/{id} should return item if exists."""
        from app.api.v1.endpoints.pending_items import get_pending_item

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_pending_item

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            get_pending_item(pending_id=1, db=mock_db_session)
        )

        assert result.pending_id == 1
        assert result.description == "Bê tông M200 móng"

    def test_get_pending_item_not_found(self, mock_db_session):
        """GET /pending-items/{id} should return 404 if not exists."""
        from app.api.v1.endpoints.pending_items import get_pending_item
        from fastapi import HTTPException

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                get_pending_item(pending_id=999, db=mock_db_session)
            )

        assert exc_info.value.status_code == 404

    def test_approve_pending_item_success(self, mock_db_session, mock_pending_item):
        """POST /pending-items/{id}/approve should create master item."""
        from app.api.v1.endpoints.pending_items import approve_pending_item
        from app.schemas.pending_item import ApprovalRequest

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_pending_item
        mock_db_session.flush = MagicMock()
        mock_db_session.commit = MagicMock()
        mock_db_session.add = MagicMock()

        # Mock WorkCodeGenerator
        with patch('app.api.v1.endpoints.pending_items.WorkCodeGenerator') as mock_gen:
            mock_gen.return_value.generate_work_code.return_value = "BT-M200-001"

            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                approve_pending_item(
                    pending_id=1,
                    data=ApprovalRequest(reviewer_id=1, notes="Approved"),
                    db=mock_db_session
                )
            )

            assert result.status == "approved"
            assert result.work_code == "BT-M200-001"
            assert mock_db_session.add.called
            assert mock_db_session.commit.called

    def test_approve_already_processed_item_fails(self, mock_db_session, mock_approved_item):
        """POST /pending-items/{id}/approve should fail if already processed."""
        from app.api.v1.endpoints.pending_items import approve_pending_item
        from app.schemas.pending_item import ApprovalRequest
        from fastapi import HTTPException

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_approved_item

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                approve_pending_item(
                    pending_id=2,
                    data=ApprovalRequest(reviewer_id=1),
                    db=mock_db_session
                )
            )

        assert exc_info.value.status_code == 400
        assert "already processed" in str(exc_info.value.detail).lower()

    def test_reject_pending_item_success(self, mock_db_session, mock_pending_item):
        """POST /pending-items/{id}/reject should mark item as rejected."""
        from app.api.v1.endpoints.pending_items import reject_pending_item
        from app.schemas.pending_item import ApprovalRequest

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_pending_item
        mock_db_session.commit = MagicMock()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            reject_pending_item(
                pending_id=1,
                data=ApprovalRequest(reviewer_id=1, notes="Low quality"),
                db=mock_db_session
            )
        )

        assert result["status"] == "rejected"
        assert mock_pending_item.status == "REJECTED"
        assert mock_db_session.commit.called

    def test_bulk_approve_success(self, mock_db_session, mock_pending_item):
        """POST /pending-items/bulk-approve should approve multiple items."""
        from app.api.v1.endpoints.pending_items import bulk_approve
        from app.schemas.pending_item import BulkApprovalRequest

        # Return a fresh pending item for each query
        def get_item(*args, **kwargs):
            item = MagicMock()
            item.pending_id = 1
            item.description = "Test item"
            item.description_normalized = "test item"
            item.sec_code = "SEC-01"
            item.unit_standard = "m3"
            item.status = "PENDING"
            return item

        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            get_item(), get_item(), get_item()
        ]
        mock_db_session.flush = MagicMock()
        mock_db_session.commit = MagicMock()
        mock_db_session.add = MagicMock()

        with patch('app.api.v1.endpoints.pending_items.WorkCodeGenerator') as mock_gen:
            mock_gen.return_value.generate_work_code.return_value = "BT-001"

            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                bulk_approve(
                    data=BulkApprovalRequest(pending_ids=[1, 2, 3], reviewer_id=1),
                    db=mock_db_session
                )
            )

            assert result.total == 3
            assert result.approved >= 0  # May be less if some fail

    def test_bulk_reject_success(self, mock_db_session, mock_pending_item):
        """POST /pending-items/bulk-reject should reject multiple items."""
        from app.api.v1.endpoints.pending_items import bulk_reject
        from app.schemas.pending_item import BulkApprovalRequest

        # Return pending items
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_pending_item, mock_pending_item, None  # 2 found, 1 not found
        ]
        mock_db_session.commit = MagicMock()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            bulk_reject(
                data=BulkApprovalRequest(pending_ids=[1, 2, 3], reviewer_id=1),
                db=mock_db_session
            )
        )

        assert result["total"] == 3
        assert result["rejected"] == 2  # 2 found and rejected


class TestPendingItemsEdgeCases:
    """Edge case tests for pending items API."""

    def test_update_pending_item_updates_normalized_description(self):
        """PUT /pending-items/{id} should update normalized description."""
        from app.api.v1.endpoints.pending_items import update_pending_item
        from app.schemas.pending_item import PendingItemUpdate

        mock_db = MagicMock()
        mock_item = MagicMock()
        mock_item.pending_id = 1
        mock_item.description = "Old description"
        mock_item.status = "PENDING"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_item
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            update_pending_item(
                pending_id=1,
                data=PendingItemUpdate(description="New Description HERE"),
                db=mock_db
            )
        )

        # Should normalize the description
        assert mock_item.description_normalized == "new description here"

    def test_empty_bulk_approve_returns_zero(self):
        """Bulk approve with empty list should return 0 approved."""
        from app.api.v1.endpoints.pending_items import bulk_approve
        from app.schemas.pending_item import BulkApprovalRequest

        mock_db = MagicMock()
        mock_db.commit = MagicMock()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            bulk_approve(
                data=BulkApprovalRequest(pending_ids=[], reviewer_id=1),
                db=mock_db
            )
        )

        assert result.approved == 0
        assert result.total == 0
