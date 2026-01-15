from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.sec_code import SECCode

router = APIRouter()


@router.get("/")
async def get_sec_codes(
    level: Optional[int] = None,
    parent_code: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get SEC codes with optional filters
    """
    query = db.query(SECCode)
    
    if is_active:
        query = query.filter(SECCode.is_active == True)
    if level is not None:
        query = query.filter(SECCode.level == level)
    if parent_code:
        query = query.filter(SECCode.parent_code == parent_code)
    
    sec_codes = query.order_by(SECCode.sec_code).all()
    
    return {
        "sec_codes": [
            {
                "sec_code": code.sec_code,
                "sec_name_vi": code.sec_name_vi,
                "sec_name_en": code.sec_name_en,
                "parent_code": code.parent_code,
                "level": code.level,
                "is_active": code.is_active
            }
            for code in sec_codes
        ],
        "total": len(sec_codes)
    }


@router.get("/{sec_code}")
async def get_sec_code(
    sec_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get SEC code details"""
    code = db.query(SECCode).filter(SECCode.sec_code == sec_code).first()
    
    if not code:
        raise HTTPException(status_code=404, detail="SEC code not found")
    
    return {
        "sec_code": code.sec_code,
        "sec_name_vi": code.sec_name_vi,
        "sec_name_en": code.sec_name_en,
        "parent_code": code.parent_code,
        "level": code.level,
        "keywords": code.keywords,
        "description": code.description,
        "is_active": code.is_active
    }


@router.get("/{sec_code}/children")
async def get_children(
    sec_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get child SEC codes"""
    children = db.query(SECCode).filter(
        SECCode.parent_code == sec_code,
        SECCode.is_active == True
    ).all()
    
    return {
        "parent_code": sec_code,
        "children": [
            {
                "sec_code": code.sec_code,
                "sec_name_vi": code.sec_name_vi,
                "sec_name_en": code.sec_name_en,
                "level": code.level
            }
            for code in children
        ]
    }


@router.get("/tree/hierarchy")
async def get_hierarchy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complete SEC code hierarchy tree
    """
    # Get all active SEC codes
    all_codes = db.query(SECCode).filter(SECCode.is_active == True).all()
    
    # Build hierarchy
    code_map = {code.sec_code: code for code in all_codes}
    tree = []
    
    for code in all_codes:
        if code.parent_code is None or code.parent_code not in code_map:
            # Root level
            tree.append({
                "sec_code": code.sec_code,
                "sec_name_vi": code.sec_name_vi,
                "sec_name_en": code.sec_name_en,
                "level": code.level,
                "children": _build_children(code.sec_code, code_map)
            })
    
    return {"hierarchy": tree}


def _build_children(parent_code: str, code_map: dict) -> list:
    """Recursively build children tree"""
    children = []
    for code in code_map.values():
        if code.parent_code == parent_code:
            children.append({
                "sec_code": code.sec_code,
                "sec_name_vi": code.sec_name_vi,
                "sec_name_en": code.sec_name_en,
                "level": code.level,
                "children": _build_children(code.sec_code, code_map)
            })
    return children
