"""
AI Structured Output Schema

Pydantic models for structured output from LLM normalization.
Used with Gemini's responseMimeType: "application/json" + responseSchema.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class StructuredWorkItem(BaseModel):
    """Structured output for a single work item from LLM."""
    group: str = Field(
        ...,
        description="Work group code: CONC, RBAR, FWRK, PIPE, ELEC, HVAC, ROAD, ERTH, FNSH, MISC",
        examples=["CONC", "RBAR", "PIPE", "ELEC"],
    )
    type: str = Field(
        ...,
        description="Work type code: STR (structural), LEA (leak/waterproof), SUP (supply), INS (install), EXC (excavate)",
        examples=["STR", "LEA", "SUP", "INS"],
    )
    location: Optional[str] = Field(
        None,
        description="Structural location: COL (column), BEM (beam), SLB (slab), FND (foundation), WAL (wall)",
        examples=["COL", "BEM", "SLB"],
    )
    grade: Optional[str] = Field(
        None,
        description="Material grade: M200, M350, CB400V, PN16, etc.",
        examples=["M350", "CB400V", "PN16"],
    )
    material: Optional[str] = Field(
        None,
        description="Material type: RDMX (ready-mix), HDPE, XLPE, PPR, PVC, Cu, Steel",
        examples=["RDMX", "HDPE", "Cu"],
    )
    dimension: Optional[str] = Field(
        None,
        description="Dimensions: D110, 4x16mm2, 600x600, etc.",
        examples=["D110", "4x16mm2", "600x600"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score 0.0-1.0",
    )
    ambiguous_fields: List[str] = Field(
        default_factory=list,
        description="List of fields that are ambiguous or uncertain",
    )
    normalized_description: str = Field(
        ...,
        description="Normalized description in standard 3-component format",
    )


class StructuredBatchRequest(BaseModel):
    """Request for batch structured normalization."""
    items: List[dict] = Field(
        ...,
        description="List of items with 'description' and optional 'wbs_context'",
    )


class StructuredBatchResponse(BaseModel):
    """Response from batch structured normalization."""
    results: List[StructuredWorkItem]
    total_items: int
    avg_confidence: float


# Gemini JSON schema for responseSchema parameter
GEMINI_STRUCTURED_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "group": {
                "type": "STRING",
                "description": "Work group code: CONC, RBAR, FWRK, PIPE, ELEC, HVAC, ROAD, ERTH, FNSH, MISC"
            },
            "type": {
                "type": "STRING",
                "description": "Work type: STR, LEA, SUP, INS, EXC"
            },
            "location": {
                "type": "STRING",
                "description": "Location: COL, BEM, SLB, FND, WAL (nullable)",
                "nullable": True
            },
            "grade": {
                "type": "STRING",
                "description": "Grade: M200, CB400V, PN16 (nullable)",
                "nullable": True
            },
            "material": {
                "type": "STRING",
                "description": "Material: RDMX, HDPE, Cu (nullable)",
                "nullable": True
            },
            "dimension": {
                "type": "STRING",
                "description": "Dimension: D110, 4x16mm2 (nullable)",
                "nullable": True
            },
            "confidence": {
                "type": "NUMBER",
                "description": "Confidence 0.0-1.0"
            },
            "ambiguous_fields": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Fields that are ambiguous"
            },
            "normalized_description": {
                "type": "STRING",
                "description": "Normalized description"
            }
        },
        "required": ["group", "type", "confidence", "normalized_description"]
    }
}
