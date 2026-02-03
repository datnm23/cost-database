"""
API Endpoints for Price History
Provides price drill-down functionality for investor transparency
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.price_history import PriceHistory, ProjectTypeEnum
from app.models.master_work_item import MasterWorkItem
from app.models.project import Project
from app.models.boq_file import BOQFile

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

class PriceDistribution(BaseModel):
    min: float
    max: float
    avg: float
    median: float
    count: int
    p25: Optional[float] = None
    p75: Optional[float] = None


class SourceProject(BaseModel):
    project_id: int
    project_name: str
    project_code: str
    project_type: Optional[str]
    region: Optional[str]
    unit_price: float
    quantity: Optional[float]
    recorded_at: str
    file_name: str


class PriceHistoryResponse(BaseModel):
    master_item_id: int
    work_code: str
    description: str
    distribution: PriceDistribution
    source_projects: List[SourceProject]
    total_records: int


# ==============================================
# Endpoints
# ==============================================

@router.get("/{master_id}/price-history", response_model=PriceHistoryResponse)
def get_price_history(
    master_id: int,
    region: Optional[str] = None,
    project_type: Optional[str] = Query(None, pattern="^(residential|commercial|industrial|infrastructure)$"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get price history for a master work item

    Returns:
    - Price distribution statistics (min, max, avg, median, percentiles)
    - List of source projects with individual prices
    - Filters for region, project type, and date range

    This endpoint helps build trust with investors by showing price sources.
    """
    # Verify master item exists
    master_item = db.query(MasterWorkItem).filter(
        MasterWorkItem.master_id == master_id
    ).first()

    if not master_item:
        raise HTTPException(status_code=404, detail="Master item not found")

    # Build query
    query = db.query(PriceHistory).filter(
        PriceHistory.master_item_id == master_id
    )

    # Apply filters
    if region:
        query = query.filter(PriceHistory.region == region)
    if project_type:
        query = query.filter(PriceHistory.project_type == project_type)
    if date_from:
        query = query.filter(PriceHistory.recorded_at >= date_from)
    if date_to:
        query = query.filter(PriceHistory.recorded_at <= date_to)

    # Get total count
    total_records = query.count()

    # If no records, return empty distribution
    if total_records == 0:
        return PriceHistoryResponse(
            master_item_id=master_id,
            work_code=master_item.work_code,
            description=master_item.description,
            distribution=PriceDistribution(
                min=0, max=0, avg=0, median=0, count=0
            ),
            source_projects=[],
            total_records=0
        )

    # Calculate distribution statistics
    stats = db.query(
        func.min(PriceHistory.unit_price).label('min_price'),
        func.max(PriceHistory.unit_price).label('max_price'),
        func.avg(PriceHistory.unit_price).label('avg_price'),
        func.count(PriceHistory.price_id).label('count')
    ).filter(
        PriceHistory.master_item_id == master_id
    )

    if region:
        stats = stats.filter(PriceHistory.region == region)
    if project_type:
        stats = stats.filter(PriceHistory.project_type == project_type)
    if date_from:
        stats = stats.filter(PriceHistory.recorded_at >= date_from)
    if date_to:
        stats = stats.filter(PriceHistory.recorded_at <= date_to)

    stats_result = stats.first()

    # Get all prices for percentile calculation
    all_prices = db.query(PriceHistory.unit_price).filter(
        PriceHistory.master_item_id == master_id
    )
    if region:
        all_prices = all_prices.filter(PriceHistory.region == region)
    if project_type:
        all_prices = all_prices.filter(PriceHistory.project_type == project_type)
    if date_from:
        all_prices = all_prices.filter(PriceHistory.recorded_at >= date_from)
    if date_to:
        all_prices = all_prices.filter(PriceHistory.recorded_at <= date_to)

    prices = sorted([float(p[0]) for p in all_prices.all()])

    # Calculate median and percentiles
    n = len(prices)
    median = prices[n // 2] if n % 2 == 1 else (prices[n // 2 - 1] + prices[n // 2]) / 2
    p25 = prices[n // 4] if n >= 4 else None
    p75 = prices[3 * n // 4] if n >= 4 else None

    distribution = PriceDistribution(
        min=float(stats_result.min_price),
        max=float(stats_result.max_price),
        avg=round(float(stats_result.avg_price), 2),
        median=round(median, 2),
        count=stats_result.count,
        p25=round(p25, 2) if p25 else None,
        p75=round(p75, 2) if p75 else None
    )

    # Get source projects with pagination
    records = query.join(Project).join(BOQFile).order_by(
        PriceHistory.recorded_at.desc()
    ).offset(skip).limit(limit).all()

    source_projects = []
    for record in records:
        project = record.project
        boq_file = record.boq_file
        source_projects.append(SourceProject(
            project_id=project.project_id,
            project_name=project.project_name,
            project_code=project.project_code,
            project_type=record.project_type.value if record.project_type else None,
            region=record.region,
            unit_price=float(record.unit_price),
            quantity=float(record.quantity) if record.quantity else None,
            recorded_at=record.recorded_at.isoformat() if record.recorded_at else None,
            file_name=boq_file.file_name
        ))

    return PriceHistoryResponse(
        master_item_id=master_id,
        work_code=master_item.work_code,
        description=master_item.description,
        distribution=distribution,
        source_projects=source_projects,
        total_records=total_records
    )


@router.get("/{master_id}/price-history/regions")
def get_available_regions(
    master_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available regions for a master item's price history
    """
    regions = db.query(PriceHistory.region).filter(
        PriceHistory.master_item_id == master_id,
        PriceHistory.region.isnot(None)
    ).distinct().all()

    return {
        "master_item_id": master_id,
        "regions": [r[0] for r in regions if r[0]]
    }


@router.get("/{master_id}/price-history/chart-data")
def get_price_chart_data(
    master_id: int,
    bucket_count: int = Query(10, ge=5, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get price distribution data formatted for histogram chart

    Returns buckets with price ranges and counts for visualization
    """
    # Get min and max prices
    stats = db.query(
        func.min(PriceHistory.unit_price).label('min_price'),
        func.max(PriceHistory.unit_price).label('max_price'),
        func.count(PriceHistory.price_id).label('total')
    ).filter(
        PriceHistory.master_item_id == master_id
    ).first()

    if not stats.total or stats.total == 0:
        return {
            "master_item_id": master_id,
            "buckets": [],
            "total": 0
        }

    min_price = float(stats.min_price)
    max_price = float(stats.max_price)

    # Handle case where all prices are the same
    if min_price == max_price:
        return {
            "master_item_id": master_id,
            "buckets": [{
                "range_start": min_price,
                "range_end": max_price,
                "count": stats.total,
                "percentage": 100.0
            }],
            "total": stats.total
        }

    # Calculate bucket size
    bucket_size = (max_price - min_price) / bucket_count

    # Get all prices
    prices = [float(p[0]) for p in db.query(PriceHistory.unit_price).filter(
        PriceHistory.master_item_id == master_id
    ).all()]

    # Create buckets
    buckets = []
    for i in range(bucket_count):
        range_start = min_price + (i * bucket_size)
        range_end = min_price + ((i + 1) * bucket_size)

        # Count prices in this bucket
        if i == bucket_count - 1:
            # Last bucket includes the max value
            count = sum(1 for p in prices if range_start <= p <= range_end)
        else:
            count = sum(1 for p in prices if range_start <= p < range_end)

        buckets.append({
            "range_start": round(range_start, 2),
            "range_end": round(range_end, 2),
            "count": count,
            "percentage": round(count / len(prices) * 100, 1) if prices else 0
        })

    return {
        "master_item_id": master_id,
        "buckets": buckets,
        "total": len(prices),
        "min_price": min_price,
        "max_price": max_price
    }
