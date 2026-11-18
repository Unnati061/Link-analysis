"""
Pydantic schemas for request/response models.
"""

from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Request ──────────────────────────────────────────────────────────────────

class LinkAnalysisRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


# ─── Section 1: Competitor Analysis ───────────────────────────────────────────

class CompetitorDetail(BaseModel):
    name: str
    strengths: List[str]
    weaknesses: List[str]
    is_ai_suggestion: bool = True


class BrandComparison(BaseModel):
    brand_name: str
    business_overview: str
    main_category: str
    main_products_services: List[str]
    competitors: List[CompetitorDetail]
    competitive_advantages: List[str]
    market_opportunities: List[str]


# ─── Section 2: Search Queries ────────────────────────────────────────────────

class SearchQuery(BaseModel):
    query: str
    platform: Literal["Google", "Facebook", "Instagram", "LinkedIn", "X (Twitter)"]
    search_intent: str
    business_relevance: str
    target_audience: str


# ─── Section 3: SEO Improvements ─────────────────────────────────────────────

class KeywordRecommendations(BaseModel):
    primary_keyword: str
    secondary_keywords: List[str]
    long_tail_keywords: List[str]
    business_keywords: List[str]


class SeoTitle(BaseModel):
    recommended_title: str
    primary_keyword: str
    improved_structure: str


class MetaDescription(BaseModel):
    recommended_description: str
    business_summary: str
    keywords_included: List[str]


class SeoImprovement(BaseModel):
    keyword_recommendations: KeywordRecommendations
    seo_title: SeoTitle
    meta_description: MetaDescription
    additional_content_suggestions: List[str]


# ─── Section 4: Services ──────────────────────────────────────────────────────

class ServiceDetail(BaseModel):
    service_name: str
    description: str
    target_industry: str
    target_customer: str
    main_benefit: str
    is_inferred: bool


# ─── Section 5: Target Audience ───────────────────────────────────────────────

class AudienceSegment(BaseModel):
    segment_name: str
    audience_priority: Literal["primary", "secondary"]
    industry: str
    business_types: List[str]
    age_range: Optional[str] = None
    location: Optional[str] = None
    interests: List[str]
    pain_points: List[str]
    buying_behavior: str
    preferred_platforms: List[str]
    marketing_recommendation: str


# ─── LLM Recommendation ───────────────────────────────────────────────────────

class LlmModelInfo(BaseModel):
    provider: str
    model_name: str
    estimated_cost_per_analysis: str
    expected_response_time: str
    reason_for_selection: str
    fallback_model: str
    recommended_approach: str


# ─── Full Analysis Response ───────────────────────────────────────────────────

class LinkAnalysisResponse(BaseModel):
    url: str
    status: str = "success"
    brand_and_competitor_analysis: BrandComparison
    top_search_queries: List[SearchQuery] = Field(min_length=5, max_length=5)
    seo_improvement: SeoImprovement
    top_services: List[ServiceDetail] = Field(min_length=5, max_length=5)
    target_audience: List[AudienceSegment] = Field(min_length=2)
    llm_recommendation: LlmModelInfo

    @model_validator(mode="after")
    def validate_required_coverage(self) -> "LinkAnalysisResponse":
        required_platforms = {"Google", "Facebook", "Instagram", "LinkedIn", "X (Twitter)"}
        actual_platforms = {query.platform for query in self.top_search_queries}
        if actual_platforms != required_platforms:
            raise ValueError("Search queries must cover each required platform exactly once.")

        audience_priorities = {segment.audience_priority for segment in self.target_audience}
        if not {"primary", "secondary"}.issubset(audience_priorities):
            raise ValueError("Target audience must include primary and secondary segments.")
        return self


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None
