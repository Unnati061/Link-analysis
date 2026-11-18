"""
Tests for the Link Analysis API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError

from app.main import app
from app.utils.validators import validate_url
from app.services.website_extractor import WebsiteExtractor
from app.schemas import LinkAnalysisResponse

client = TestClient(app)


# ── Health check ──────────────────────────────────────────────────────────────

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# ── URL Validation ─────────────────────────────────────────────────────────────

def test_missing_url():
    response = client.post("/link-analysis", json={})
    assert response.status_code == 422  # Pydantic validation error


def test_invalid_url_scheme():
    response = client.post("/link-analysis", json={"url": "ftp://example.com"})
    assert response.status_code in (400, 422)


def test_localhost_blocked():
    response = client.post("/link-analysis", json={"url": "http://localhost/admin"})
    assert response.status_code == 400
    assert "local" in response.json().get("message", "").lower()


def test_private_ip_blocked():
    response = client.post("/link-analysis", json={"url": "http://192.168.1.1/"})
    assert response.status_code == 400


def test_internal_ip_blocked():
    response = client.post("/link-analysis", json={"url": "http://10.0.0.1/"})
    assert response.status_code == 400


def test_modern_long_tld_is_accepted(monkeypatch):
    monkeypatch.setattr(
        "app.utils.validators.socket.getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 443))],
    )
    assert validate_url("https://example.technology") == (True, "")


def test_nonstandard_port_is_rejected():
    assert validate_url("http://example.com:8080/")[0] is False
    assert validate_url("http://example.com:443/")[0] is False


def test_ipv6_loopback_is_blocked():
    assert validate_url("http://[::1]/")[0] is False


@pytest.mark.asyncio
async def test_redirect_to_local_address_is_blocked(monkeypatch):
    class RedirectResponse:
        status_code = 302
        headers = {"location": "http://127.0.0.1/admin"}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        def stream(self, method, url):
            return RedirectResponse()

    monkeypatch.setattr("app.services.website_extractor.httpx.AsyncClient", FakeClient)
    monkeypatch.setattr(
        "app.services.website_extractor.validate_url",
        lambda url: (False, "Access to private/internal addresses is not allowed.")
        if "127.0.0.1" in url else (True, ""),
    )

    with pytest.raises(ValueError, match="private/internal"):
        await WebsiteExtractor().extract("https://public.example")


# ── Successful Analysis (mocked) ───────────────────────────────────────────────

MOCK_WEBSITE_DATA = {
    "url": "https://example.com",
    "domain": "example.com",
    "title": "Example Domain",
    "meta_description": "Example company website",
    "meta_keywords": "",
    "site_name": "example.com",
    "headings": {"h1": ["Example Domain"], "h2": [], "h3": []},
    "body_text": "This domain is for use in illustrative examples in documents.",
    "links": [],
    "structured_content": [],
}

MOCK_LLM_RESPONSE = {
    "brand_and_competitor_analysis": {
        "brand_name": "Example Domain",
        "business_overview": "A sample domain used for documentation and testing.",
        "main_category": "Technology / Documentation",
        "main_products_services": ["Domain examples", "Documentation samples"],
        "competitors": [
            {"name": "IANA", "strengths": ["Authority"], "weaknesses": ["Limited services"]},
            {"name": "W3C", "strengths": ["Standards body"], "weaknesses": ["Slow adoption"]},
            {"name": "MDN Web Docs", "strengths": ["Comprehensive docs"], "weaknesses": ["No commercial offering"]},
        ],
        "competitive_advantages": ["Simplicity", "Universal recognition"],
        "market_opportunities": ["Expand to developer tools", "Create interactive examples"],
    },
    "top_search_queries": [
        {"query": "example domain documentation", "platform": "Google", "search_intent": "Informational", "business_relevance": "High", "target_audience": "Developers"},
        {"query": "sample domain for testing", "platform": "Facebook", "search_intent": "Discovery", "business_relevance": "Medium", "target_audience": "Tech community"},
        {"query": "web example domain", "platform": "Instagram", "search_intent": "Inspiration", "business_relevance": "Low", "target_audience": "Students"},
        {"query": "IANA example domain uses", "platform": "LinkedIn", "search_intent": "B2B Research", "business_relevance": "High", "target_audience": "IT Professionals"},
        {"query": "example.com use cases", "platform": "X (Twitter)", "search_intent": "Awareness", "business_relevance": "Medium", "target_audience": "Developers"},
    ],
    "seo_improvement": {
        "keyword_recommendations": {
            "primary_keyword": "example domain",
            "secondary_keywords": ["sample domain", "test domain", "dummy URL"],
            "long_tail_keywords": ["how to use example.com in documentation", "IANA reserved domain example"],
            "business_keywords": ["web documentation", "domain examples", "RFC reserved domains"],
        },
        "seo_title": {
            "recommended_title": "Example Domain | Official IANA Sample Domain for Documentation",
            "primary_keyword": "example domain",
            "improved_structure": "Primary Keyword | Brand Benefit | Brand Name",
        },
        "meta_description": {
            "recommended_description": "Use Example Domain for illustrative examples in documents and testing. An IANA-reserved domain for official documentation purposes.",
            "business_summary": "Official sample domain for documentation and testing.",
            "keywords_included": ["example domain", "IANA", "documentation"],
        },
        "additional_content_suggestions": [
            "Create a blog explaining RFC 2606 reserved domains",
            "Add an FAQ page about legitimate uses of example.com",
            "Create a developer guide page",
            "Add a 'Related Resources' page linking to IANA and W3C",
            "Publish case studies on how documentation teams use example.com",
        ],
    },
    "top_services": [
        {"service_name": "Domain Example Service", "description": "Provides a safe, reserved domain for documentation.", "target_industry": "Technology", "target_customer": "Developers", "main_benefit": "Avoid accidental real-domain references", "is_inferred": True},
        {"service_name": "Documentation Testing", "description": "Use this domain in test scripts safely.", "target_industry": "Software Development", "target_customer": "QA Engineers", "main_benefit": "Safe placeholder URL", "is_inferred": True},
        {"service_name": "RFC Compliance Reference", "description": "Reference domain for RFC compliance examples.", "target_industry": "Networking", "target_customer": "Network Engineers", "main_benefit": "Standards-compliant examples", "is_inferred": True},
        {"service_name": "Educational Examples", "description": "Used in textbooks and courses.", "target_industry": "Education", "target_customer": "Instructors", "main_benefit": "Neutral, universally recognized URL", "is_inferred": True},
        {"service_name": "API Testing Placeholder", "description": "Safe URL for API integration tests.", "target_industry": "API Development", "target_customer": "Backend Developers", "main_benefit": "No side-effects from test calls", "is_inferred": True},
    ],
    "target_audience": [
        {"segment_name": "Software Developers", "audience_priority": "primary", "industry": "Software", "business_types": ["Software teams", "Independent developers"], "age_range": "", "location": "Global", "interests": ["Coding", "Open source"], "pain_points": ["Finding safe test URLs"], "buying_behavior": "Research-driven", "preferred_platforms": ["GitHub", "Stack Overflow", "LinkedIn"], "marketing_recommendation": "Publish developer documentation and sample integrations."},
        {"segment_name": "Technical Writers", "audience_priority": "secondary", "industry": "Publishing", "business_types": ["Documentation teams", "Technical publishers"], "age_range": "", "location": "Global", "interests": ["Documentation", "Standards"], "pain_points": ["Realistic examples without exposing real URLs"], "buying_behavior": "Tool-focused", "preferred_platforms": ["LinkedIn", "Medium"], "marketing_recommendation": "Share standards-based writing guides and examples."},
    ],
    "llm_recommendation": {
        "provider": "Google",
        "model_name": "gemini-3.1-flash-lite",
        "estimated_cost_per_analysis": "Depends on actual token usage; see README",
        "expected_response_time": "Not benchmarked",
        "reason_for_selection": "Selected for low token pricing, 1M-token context and native JSON output; accuracy needs evaluation.",
        "fallback_model": "gpt-6-luna",
        "recommended_approach": "Use Gemini Flash-Lite as primary with response caching; GPT-6 Luna is an alternative provider.",
    },
}


@patch("app.main.validate_url", return_value=(True, ""))
@patch("app.services.website_extractor.WebsiteExtractor.extract", new_callable=AsyncMock)
@patch("app.services.llm_service.LLMService.generate", new_callable=AsyncMock)
def test_successful_analysis(mock_llm, mock_extract, mock_validate):
    mock_extract.return_value = MOCK_WEBSITE_DATA
    mock_llm.return_value = MOCK_LLM_RESPONSE

    response = client.post("/link-analysis", json={"url": "https://example.com"})
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["url"] == "https://example.com"

    # Check all 5 sections are present
    assert "brand_and_competitor_analysis" in data
    assert "top_search_queries" in data
    assert "seo_improvement" in data
    assert "top_services" in data
    assert "target_audience" in data
    assert "llm_recommendation" in data

    # Validate section 1
    bca = data["brand_and_competitor_analysis"]
    assert bca["brand_name"] == "Example Domain"
    assert len(bca["competitors"]) >= 3
    assert all(c["is_ai_suggestion"] for c in bca["competitors"])

    # Validate section 2 — 5 queries
    assert len(data["top_search_queries"]) == 5
    platforms = {q["platform"] for q in data["top_search_queries"]}
    assert platforms == {"Google", "Facebook", "Instagram", "LinkedIn", "X (Twitter)"}

    # Validate section 3
    seo = data["seo_improvement"]
    assert "keyword_recommendations" in seo
    assert "seo_title" in seo
    assert "meta_description" in seo
    assert len(seo["additional_content_suggestions"]) >= 3

    # Validate section 4 — 5 services
    assert len(data["top_services"]) == 5

    # Validate section 5
    assert len(data["target_audience"]) >= 2
    assert {a["audience_priority"] for a in data["target_audience"]} >= {"primary", "secondary"}

    invalid_data = dict(data)
    invalid_data["top_search_queries"] = [dict(query) for query in data["top_search_queries"]]
    invalid_data["top_search_queries"][0]["platform"] = "LinkedIn"
    with pytest.raises(ValidationError):
        LinkAnalysisResponse.model_validate(invalid_data)


@patch("app.main.validate_url", return_value=(True, ""))
@patch("app.services.website_extractor.WebsiteExtractor.extract", new_callable=AsyncMock)
def test_inaccessible_website(mock_extract, mock_validate):
    mock_extract.side_effect = ValueError("HTTP 403 error fetching https://blocked.example.com")
    response = client.post("/link-analysis", json={"url": "https://blocked.example.com"})
    assert response.status_code == 400
    assert "error" in response.json().get("status", "")


@patch("app.main.validate_url", return_value=(True, ""))
@patch("app.services.website_extractor.WebsiteExtractor.extract", new_callable=AsyncMock)
@patch("app.services.analysis_service.AnalysisService.analyze", new_callable=AsyncMock)
def test_provider_failure_is_sanitized(mock_analyze, mock_extract, mock_validate):
    mock_extract.return_value = MOCK_WEBSITE_DATA
    mock_analyze.side_effect = RuntimeError("private provider response details")

    response = client.post("/link-analysis", json={"url": "https://example.com"})

    assert response.status_code == 502
    assert response.json() == {
        "status": "error",
        "message": "LLM provider failed. Verify the API key, model access, and quota.",
    }
    assert "private provider response details" not in response.text
