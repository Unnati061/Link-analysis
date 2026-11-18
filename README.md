# AI-Powered Website Link Analysis API

A FastAPI application that analyzes any website URL and returns structured business intelligence using LLMs (Google Gemini / OpenAI / Anthropic).

---

## Features

- **5 structured analysis sections** per website:
  1. Competitor vs Your Brand Details
  2. Top 5 Target Search Queries (Google, Facebook, Instagram, LinkedIn, X)
  3. SEO Improvement (keywords, title, meta description, content suggestions)
  4. Top 5 Services
  5. Target Audience Identification
- **Multi-LLM support**: Google Gemini, OpenAI GPT-6 Luna, Anthropic Claude Haiku
- **SSRF protection**: rejects non-public IPv4/IPv6 destinations, rechecks redirects, restricts ports, and ignores environment proxy settings
- **Graceful error handling** for inaccessible URLs and API failures
- **Fully typed** Pydantic v2 schemas
- Interactive Swagger UI at `/docs`

---

## LLM Model Recommendation

Prices below are provider list prices checked on 18 November 2026. Prices are USD per million tokens; actual cost per request depends on token use and account tier. Response-time and comparative accuracy benchmarks have not been run for this project.

| Provider | Model | Input / output price | Context | JSON support | Accuracy / speed evidence |
|---|---|---:|---:|---|---|
| **Google** | `gemini-3.1-flash-lite` | $0.25 / $1.50 | 1M tokens | Native JSON response mode | Not benchmarked here; provider positions it for low latency and extraction |
| OpenAI | `gpt-6-luna` | $0.05 / $0.25 | 1.05M tokens | Structured outputs / JSON mode | Not benchmarked here; provider positions it for efficient high-volume tasks |
| Anthropic | `claude-haiku-4-5-20251001` | $1 / $5 | 200K tokens | Structured output support | Not benchmarked here; provider positions it as fast |

**Recommendation:** Start with Gemini 3.1 Flash-Lite because the application needs a long context window, structured JSON, and low-cost single-pass analysis. This is a cost and capability choice, not a claim that it has the highest accuracy. Run a representative labeled evaluation set and measure latency before making quality or speed claims. Treat competitor names, strengths, and weaknesses as AI suggestions unless independently verified with credible sources.

For a rough cost illustration, a request using 4,000 input tokens and 1,500 output tokens costs about **$0.00325** on Gemini 3.1 Flash-Lite at the listed standard rates (0.004 × $0.25 + 0.0015 × $1.50). Replace these assumed token counts with measured usage for production estimates.

Cost controls: strip navigation and repeated text, cap extracted content, avoid repeat requests with a cache keyed by normalized URL and content hash, and use a cheaper model only after checking output quality. No search volume or ranking data is returned because the app does not call a keyword-data provider.

Pricing/model references: [Gemini 3.1 Flash-Lite model card](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite) and [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing), [GPT-6 Luna model card](https://developers.openai.com/api/docs/models/gpt-6-luna) and [OpenAI API pricing](https://developers.openai.com/api/docs/pricing), [Claude Haiku 4.5 model card](https://platform.claude.com/docs/en/models/haiku-4-5/overview) and [Anthropic Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing).

---

## Project Structure

```
ai-link-analysis/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app & routes
│   ├── config.py         # Environment settings
│   ├── schemas.py        # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── website_extractor.py  # Fetch & parse website HTML
│   │   ├── llm_service.py        # LLM provider wrapper
│   │   └── analysis_service.py   # Prompt builder & response mapper
│   └── utils/
│       ├── __init__.py
│       └── validators.py         # URL & SSRF validation
├── tests/
│   ├── __init__.py
│   └── test_link_analysis.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### 1. Clone / Download

```bash
cd "Dxora crest python assignment"
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
copy .env.example .env
```

Edit `.env` and set your LLM API key:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 5. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

The API will be available at: **http://localhost:4000**  
Swagger docs: **http://localhost:4000/docs**

---

## API Reference

### `POST /link-analysis`

Analyze a website and return structured business intelligence.

**Request:**

```http
POST http://localhost:4000/link-analysis
Content-Type: application/json

{
  "url": "https://example.com"
}
```

**Response (200 OK):**

The following illustrative response shows the response shape; competitor entries are explicitly unverified AI suggestions.

```json
{
  "url": "https://example.com",
  "status": "success",
  "brand_and_competitor_analysis": {
    "brand_name": "Example Corp",
    "business_overview": "...",
    "main_category": "Technology / SaaS",
    "main_products_services": ["Product A", "Service B", "Solution C"],
    "competitors": [
      {
        "name": "Competitor X",
        "strengths": ["Strong brand", "Wide reach"],
        "weaknesses": ["High pricing", "Poor support"],
        "is_ai_suggestion": true
      },
      {
        "name": "Competitor Y",
        "strengths": ["Established offering"],
        "weaknesses": ["Narrow focus"],
        "is_ai_suggestion": true
      },
      {
        "name": "Competitor Z",
        "strengths": ["Recognized brand"],
        "weaknesses": ["Limited customization"],
        "is_ai_suggestion": true
      }
    ],
    "competitive_advantages": ["Affordable pricing", "Local support"],
    "market_opportunities": ["Expand to SME market", "Mobile-first approach"]
  },
  "top_search_queries": [
    {
      "query": "best web development company India",
      "platform": "Google",
      "search_intent": "Service Search",
      "business_relevance": "High",
      "target_audience": "Small business owners"
    },
    {
      "query": "affordable website design services",
      "platform": "Facebook",
      "search_intent": "Business Discovery",
      "business_relevance": "High",
      "target_audience": "Entrepreneurs"
    },
    {
      "query": "website design inspiration for small business",
      "platform": "Instagram",
      "search_intent": "Inspiration",
      "business_relevance": "Medium",
      "target_audience": "Small business owners"
    },
    {
      "query": "web development partner for startups",
      "platform": "LinkedIn",
      "search_intent": "B2B service search",
      "business_relevance": "High",
      "target_audience": "Startup decision makers"
    },
    {
      "query": "custom website development services",
      "platform": "X (Twitter)",
      "search_intent": "Service discovery",
      "business_relevance": "Medium",
      "target_audience": "Entrepreneurs"
    }
  ],
  "seo_improvement": {
    "keyword_recommendations": {
      "primary_keyword": "web development company",
      "secondary_keywords": ["website design", "custom software development"],
      "long_tail_keywords": ["affordable web development for small businesses"],
      "business_keywords": ["digital transformation", "IT solutions"]
    },
    "seo_title": {
      "recommended_title": "Web Development Company | Affordable Custom Solutions | Example Corp",
      "primary_keyword": "web development company",
      "improved_structure": "Primary Keyword | Value Proposition | Brand"
    },
    "meta_description": {
      "recommended_description": "Example Corp offers affordable web development and digital solutions for small businesses. Get a free quote today.",
      "business_summary": "Affordable web development for small businesses.",
      "keywords_included": ["web development", "small businesses", "affordable"]
    },
    "additional_content_suggestions": [
      "Service landing pages for each technology stack",
      "Industry-specific case study pages",
      "FAQ page about pricing and timelines",
      "Blog: 'Top 10 Web Development Trends'",
      "Location-based landing pages for target cities"
    ]
  },
  "top_services": [
    {
      "service_name": "Custom Web Development",
      "description": "End-to-end web application development tailored to business needs.",
      "target_industry": "All Industries",
      "target_customer": "SMEs and Startups",
      "main_benefit": "Scalable, custom-built digital presence",
      "is_inferred": false
    },
    {
      "service_name": "E-commerce Development",
      "description": "Builds online stores and checkout experiences.",
      "target_industry": "Retail",
      "target_customer": "Retail businesses",
      "main_benefit": "Sell products online",
      "is_inferred": true
    },
    {
      "service_name": "Website Design",
      "description": "Designs responsive business websites.",
      "target_industry": "Professional services",
      "target_customer": "Small businesses",
      "main_benefit": "Improve online presence",
      "is_inferred": true
    },
    {
      "service_name": "Website Maintenance",
      "description": "Maintains and updates business websites.",
      "target_industry": "All industries",
      "target_customer": "Website owners",
      "main_benefit": "Keep websites current and reliable",
      "is_inferred": true
    },
    {
      "service_name": "Search Optimization",
      "description": "Improves technical and on-page search visibility.",
      "target_industry": "All industries",
      "target_customer": "Businesses seeking organic traffic",
      "main_benefit": "Increase relevant search discovery",
      "is_inferred": true
    }
  ],
  "target_audience": [
    {
      "segment_name": "Small Business Owners",
      "audience_priority": "primary",
      "industry": "Professional services and retail",
      "business_types": ["Local businesses", "Small online retailers"],
      "age_range": "30-55",
      "location": "India",
      "interests": ["Business growth", "Digital tools"],
      "pain_points": ["High agency costs", "Long delivery times"],
      "buying_behavior": "Price-sensitive, referral-driven",
      "preferred_platforms": ["Google", "Facebook", "WhatsApp"],
      "marketing_recommendation": "Use local case studies and clear service packages."
    },
    {
      "segment_name": "Startup Decision Makers",
      "audience_priority": "secondary",
      "industry": "Technology",
      "business_types": ["Early-stage startups", "Software companies"],
      "age_range": null,
      "location": null,
      "interests": ["Product launches", "Business growth"],
      "pain_points": ["Limited in-house development capacity"],
      "buying_behavior": "Research-driven and milestone-focused",
      "preferred_platforms": ["Google", "LinkedIn"],
      "marketing_recommendation": "Publish startup-focused project examples and delivery timelines."
    }
  ],
  "llm_recommendation": {
    "provider": "Google",
    "model_name": "gemini-3.1-flash-lite",
    "estimated_cost_per_analysis": "Estimate depends on actual tokens; see README",
    "expected_response_time": "Not benchmarked",
    "reason_for_selection": "Selected for low token pricing, 1M-token context and native structured JSON support; accuracy must be benchmarked.",
    "fallback_model": "gpt-6-luna",
    "recommended_approach": "Use Gemini Flash-Lite as primary with response caching for repeated URLs. Configure GPT-6 Luna as an alternative provider when needed."
  }
}
```

**Error Response (400):**

```json
{
  "status": "error",
  "message": "Access to private/internal addresses is not allowed."
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

The latest test run is recorded in [verification/test-results.txt](verification/test-results.txt). The suite uses mocked LLM responses. The original local Gemini project had no usable request quota; a replacement key was later verified with a live structured JSON request and must be configured as `GEMINI_API_KEY` in the deployment dashboard. See [verification/live-check.md](verification/live-check.md).

---

## Security

- All URLs are validated before processing
- SSRF protection rejects private and other non-public IPv4/IPv6 addresses, revalidates redirects, and only allows standard HTTP(S) ports
- API keys are loaded from `.env` — never committed to version control
- `.env` is listed in `.gitignore`

---

## Deployment

**Live demo:** https://link-analysis-api.onrender.com/

**API documentation:** https://link-analysis-api.onrender.com/docs

**Analysis endpoint:** `POST https://link-analysis-api.onrender.com/link-analysis`

The repository includes `render.yaml`, which creates a Render web service with a health check at `/`. In Render, create a Blueprint from this repository and provide `GEMINI_API_KEY` when prompted. Do not paste API keys into GitHub or `render.yaml`.

After deployment, use these URLs in the submission:

```text
https://YOUR-SERVICE.onrender.com/
https://YOUR-SERVICE.onrender.com/docs
https://YOUR-SERVICE.onrender.com/link-analysis
```

For deployment on another public server:

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn + Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:4000
```

Or use a free hosting platform:
- **Railway**: https://railway.app
- **Render**: https://render.com
- **Fly.io**: https://fly.io

---

## Submission Checklist

- [x] FastAPI application with `POST /link-analysis` on port 4000
- [x] 5 structured analysis sections
- [x] LLM integration (Gemini / OpenAI / Anthropic — configurable)
- [x] SSRF protection and URL validation
- [x] Error handling for inaccessible URLs and API failures
- [x] Pydantic v2 schemas with structured JSON output
- [x] Unit tests
- [x] README with setup instructions and sample API request/response
- [x] LLM comparison and recommendation (provider list prices and assumptions documented)
- [x] Deploy to Render — https://link-analysis-api.onrender.com/
- [x] Add test and live-check logs in `verification/`

---

## Contact

Submission email: **hr@chivoxai.com**  
Subject: `Your Name - Python Practical Link Analysis test review`
