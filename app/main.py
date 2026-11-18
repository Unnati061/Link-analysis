"""
FastAPI application entry point.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas import ErrorResponse, LinkAnalysisRequest, LinkAnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.website_extractor import WebsiteExtractor
from app.utils.validators import validate_url

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI-Powered Website Link Analysis API",
    description=(
        "Analyzes a given website URL and returns structured business insights: "
        "competitor analysis, SEO recommendations, target search queries, "
        "top services, and target audience identification."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Service instances ──────────────────────────────────────────────────────────

extractor = WebsiteExtractor()
analyser = AnalysisService()


# ── Global exception handler ───────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled request error (%s)", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"},
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", summary="Health check")
async def root():
    return {
        "status": "ok",
        "service": "AI-Powered Website Link Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.post(
    "/link-analysis",
    response_model=LinkAnalysisResponse,
    summary="Analyze a website URL",
    description=(
        "Accepts a website URL, extracts its content, and uses an LLM to generate "
        "structured insights across five sections: competitor analysis, search queries, "
        "SEO improvement, top services, and target audience."
    ),
    responses={
        200: {"description": "Successful analysis"},
        400: {"model": ErrorResponse, "description": "Invalid URL or inaccessible website"},
        422: {"description": "Invalid request body"},
        502: {"model": ErrorResponse, "description": "LLM provider failure"},
    },
)
async def link_analysis(request: LinkAnalysisRequest):
    url = request.url

    # 1. Validate URL + SSRF check
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": error_msg},
        )

    # 2. Extract website content
    try:
        website_data = await extractor.extract(url)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc)},
        )

    # 3. Run LLM analysis
    try:
        result = await analyser.analyze(url, website_data)
    except Exception as exc:
        logger.error("LLM analysis failed (%s)", type(exc).__name__)
        return JSONResponse(
            status_code=502,
            content={
                "status": "error",
                "message": "LLM provider failed. Verify the API key, model access, and quota.",
            },
        )

    return result


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.app_port, reload=True)
