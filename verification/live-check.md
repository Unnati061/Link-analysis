# Live Verification

Date: 18 November 2026

- `GET /` returned HTTP 200 with `status: ok`.
- `GET /docs` returned HTTP 200.
- The website extractor fetched `https://example.com`, found the title `Example Domain`, and extracted 171 body-text characters.
- A real Gemini generation request reached Google but was rejected with HTTP 429 (`RESOURCE_EXHAUSTED`); the configured project's Generate Content request quota is 0. The API returns a sanitized HTTP 502 response for provider failures.

The unit suite in [test-results.txt](test-results.txt) uses mocked LLM output for its success path. Repeat the live analysis check after enabling Gemini quota or configuring a provider key with usable quota.
