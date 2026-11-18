# AI-Powered Website Link Analysis API

A FastAPI service that fetches a public website and uses **Google Gemini** (`gemini-3.1-flash-lite`) to return structured business, SEO, search-query, service, and audience insights.

**Live API:** https://link-analysis-api.onrender.com/

**Interactive API documentation:** https://link-analysis-api.onrender.com/docs

## What it does

Given a public website URL, the API:

- validates the URL and blocks local/private network targets;
- fetches and extracts readable website content;
- sends the extracted content to Google Gemini using a structured JSON schema; and
- returns a consistent analysis containing:
  - brand summary and AI-suggested competitors;
  - exactly five target search queries for Google, Facebook, Instagram, LinkedIn, and X;
  - SEO keyword, title, meta-description, and content recommendations;
  - exactly five services or products, with inferred entries identified;
  - primary and secondary target-audience profiles; and
  - high-level SEO and business insights.

The API does not claim that inferred data such as competitors, services, or target audiences is verified fact. These fields are clearly identified as AI-generated or inferred in the response.

## Request flow

1. Validate the supplied `http` or `https` URL.
2. Resolve and reject localhost, private, link-local, multicast, reserved, and other non-public IP addresses.
3. Download HTML with redirect validation, a response-size limit, and a timeout.
4. Extract visible page text and metadata.
5. Ask Gemini for a schema-constrained JSON analysis.
6. Validate the returned JSON before sending it to the client.

## Project structure

```text
app/
  main.py                         FastAPI application and routes
  schemas/
    request.py                    Request validation
    response.py                   Structured response models
  services/
    website_extractor.py          Safe website retrieval and text extraction
    llm_service.py                Google Gemini integration
  utils/
    validators.py                 URL, DNS, and SSRF protections
tests/                            Unit and endpoint tests
render.yaml                       Render deployment configuration
requirements.txt                  Python dependencies
```

## Requirements

- Python 3.10 or later
- A Google Gemini API key with access to `gemini-3.1-flash-lite`

## Run locally

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies and create a local environment file:

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the following values in `.env`:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to use the interactive API documentation.

## API

### `POST /link-analysis`

Request body:

```json
{
  "url": "https://example.com"
}
```

Successful responses have the following top-level shape:

```json
{
  "url": "https://example.com",
  "status": "success",
  "brand_and_competitor_analysis": {},
  "top_search_queries": [],
  "seo_improvement": {},
  "top_services": [],
  "target_audience": [],
  "llm_recommendation": {}
}
```

Key response rules:

- `top_search_queries` contains five entries, one each for Google, Facebook, Instagram, LinkedIn, and X (Twitter).
- `seo_improvement` contains keyword, title, meta-description, and content recommendations.
- `top_services` contains five entries and marks inferred entries with `is_inferred`.
- `target_audience` contains at least a primary and secondary segment, including priority, industry, business-type, and marketing-recommendation details.
- Competitor suggestions are marked with `is_ai_suggestion: true`.
- `llm_recommendation` documents the model used and the project's model-selection approach.
- The API intentionally omits unsupported search-volume and ranking claims.

Example request with PowerShell:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/link-analysis" `
  -ContentType "application/json" `
  -Body '{"url":"https://example.com"}'
```

## Gemini integration

The deployed application uses Google Gemini with the `gemini-3.1-flash-lite` model. Gemini is used for its structured-output support and large context window, which allow the service to return schema-validated analysis from extracted website content.

Cost is controlled by extracting only relevant visible text, truncating the page content before analysis, and using a lightweight model. Model capabilities, availability, and pricing can change; refer to the [Google AI pricing page](https://ai.google.dev/gemini-api/docs/pricing) for current information.

## Security safeguards

- Accepts only `http` and `https` URLs.
- Rejects localhost and non-public IP addresses after DNS resolution.
- Validates every redirect destination.
- Uses a bounded response body, explicit timeouts, and HTML-only processing.
- Does not commit `.env` files or API keys.
- Returns a generic provider error instead of exposing provider credentials or internal exception details.

## Tests

Run the automated test suite:

```powershell
pytest tests/ -q
```

The test suite covers request validation, URL and SSRF protections, redirect handling, response-schema rules, and API endpoint behavior. The current suite contains 13 passing tests.

## Deployment

The project includes `render.yaml` for deployment to Render. The service starts with:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure `GEMINI_API_KEY` as a secret environment variable in Render. The deployed API is available at https://link-analysis-api.onrender.com/.
