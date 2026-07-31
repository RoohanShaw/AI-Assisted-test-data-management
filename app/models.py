"""
models.py — Pydantic request / response schemas
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────
# Request Schemas
# ──────────────────────────────────────────────

class FieldDefinition(BaseModel):
    """A single field the caller wants test data for."""
    field_name: str = Field(..., description="Human-readable field name, e.g. 'Patient Name'")
    field_type: Literal["String", "Number", "Boolean", "Date", "Email", "Phone", "Auto"] = Field(
        default="Auto",
        description="Hint about the data type. 'Auto' lets the AI decide."
    )
    # Optional override — caller can pin a category if they already know it
    category_override: Optional[str] = Field(
        default=None,
        description="Explicitly set the semantic category (skips AI classification)."
    )

    @field_validator("field_name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field_name must not be blank")
        return v.strip()


class GenerateRequest(BaseModel):
    """Top-level request payload for POST /generate"""
    module: str = Field(
        default="Generic",
        description="Business module context, e.g. 'Registration', 'Payroll'."
    )
    record_count: int = Field(
        default=5,
        ge=1,
        le=1000,
        description="Number of records to generate."
    )
    fields: List[FieldDefinition] = Field(
        ...,
        min_length=1,
        description="Fields to generate data for."
    )
    locale: Optional[str] = Field(
        default=None,
        description="Faker locale override, e.g. 'en_US', 'de_DE'. Default is en_IN."
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible output."
    )


# ──────────────────────────────────────────────
# Internal / Classification Schemas
# ──────────────────────────────────────────────

class FieldClassification(BaseModel):
    """Result of classifying a single field."""
    field_name: str
    field_type: str
    category: str                  # semantic category, e.g. 'Human Age'
    generator: str                 # generator key, e.g. 'age', 'full_name'
    confidence: float              # 0.0–1.0
    source: Literal["faiss", "cache", "override", "fallback", "type_router"]
    rules: Dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────
# Response Schemas
# ──────────────────────────────────────────────

class FieldMetadata(BaseModel):
    """Per-field classification metadata returned in the response."""
    field_name: str
    category: str
    generator: str
    confidence: float
    source: str


class GenerateResponse(BaseModel):
    """Top-level response for POST /generate"""
    module: str
    record_count: int
    records: List[Dict[str, Any]]
    field_metadata: List[FieldMetadata] = Field(
        default_factory=list,
        description="Classification details for each field."
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings (e.g. used fallback)."
    )


class HealthResponse(BaseModel):
    status: str
    knowledge_base_size: int
    learned_cache_size: int
    faiss_index_size: int
    embedding_model: str


class KnowledgeEntry(BaseModel):
    field_name: str
    category: str
    generator: str
    source: str


class KnowledgeResponse(BaseModel):
    total: int
    entries: List[KnowledgeEntry]


class FeedbackRequest(BaseModel):
    """Allow callers to correct a misclassification."""
    field_name: str
    correct_category: str
    correct_generator: str
    module: Optional[str] = None


class FeedbackResponse(BaseModel):
    message: str
    field_name: str
    category: str
    generator: str


# ──────────────────────────────────────────────
# Template-based Pipeline Schemas
# (for POST /generate/from-json and POST /generate/from-excel)
# ──────────────────────────────────────────────

class FieldClassificationMeta(BaseModel):
    """Per-field classification metadata from the AI pipeline."""
    category: str
    generator: str
    confidence: float
    source: str


class TemplateGenerateResponse(BaseModel):
    """
    Response for POST /generate/from-json and POST /generate/from-excel.

    - output:   Populated JSON matching SampleOutput.json shape
    - metadata: Per-field AI classification details
    - warnings: Non-fatal warnings (fallback classifications, generator errors)
    """
    output: Dict[str, Any] = Field(
        description="Populated test data JSON in SampleOutput.json format"
    )
    metadata: Dict[str, FieldClassificationMeta] = Field(
        default_factory=dict,
        description="AI classification details per field name"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings"
    )


class FromJsonRequest(BaseModel):
    """
    Optional wrapper for POST /generate/from-json when sending extra options
    alongside the raw input JSON.
    """
    module: Optional[str] = Field(
        default="Generic",
        description="Business module hint for AI classification (e.g. 'Appointment')"
    )
    locale: Optional[str] = Field(
        default=None,
        description="Faker locale override, e.g. 'en_IN'. Default is en_IN."
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible output."
    )
