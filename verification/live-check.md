# Live Verification

Date: 18 November 2026

- `GET /` returned HTTP 200 with `status: ok`.
- `GET /docs` returned HTTP 200.
- The website extractor fetched `https://example.com`, found the title `Example Domain`, and extracted 171 body-text characters.
- The original local Gemini key reached Google but was rejected with HTTP 429 (`RESOURCE_EXHAUSTED`) because its project's Generate Content request quota was 0. The API returns a sanitized HTTP 502 response for provider failures.
- A replacement Gemini key was subsequently verified with a minimal live structured JSON request using `gemini-3.1-flash-lite`. The key value is not recorded in this repository and must be configured in the deployment dashboard.

The unit suite in [test-results.txt](test-results.txt) uses mocked LLM output for its success path. Repeat the full live analysis check after configuring the verified provider key in the deployment dashboard.
