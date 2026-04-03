"""
Bassi Clothing — AI Marketing Dashboard
=========================================
FastAPI-powered web dashboard for managing leads, campaigns, content, and pipeline.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

# Add parent to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

app = FastAPI(
    title="Bassi Clothing — AI Marketing Dashboard",
    description="B2B Outbound Engine, Sales Pipeline, and Content Ops",
    version="1.0.0",
)

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── Root: Serve Dashboard ───────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard loading...</h1>")


# ═══════════════════════════════════════════════════════════════
#  LEADS API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/leads")
async def api_get_leads(
    country: Optional[str] = None,
    industry: Optional[str] = None,
    stage: Optional[str] = None,
    query: Optional[str] = None,
    has_email: Optional[bool] = None,
):
    from outbound_engine.lead_manager import search_leads, get_all_leads
    if any([country, industry, stage, query, has_email is not None]):
        leads = search_leads(country=country, industry=industry, stage=stage,
                            query=query, has_email=has_email)
    else:
        leads = get_all_leads()
    return {"leads": leads, "count": len(leads)}


@app.get("/api/leads/{lead_id}")
async def api_get_lead(lead_id: str):
    from outbound_engine.lead_manager import get_lead
    lead = get_lead(lead_id)
    if lead:
        return lead
    return JSONResponse(status_code=404, content={"error": "Lead not found"})


@app.post("/api/leads/import")
async def api_import_leads(request: Request):
    body = await request.json()
    csv_path = body.get("csv_path", "")
    if not csv_path:
        # Default to Apollo CSV
        csv_path = str(BASE_DIR.parent / "Appolo_Scraper" / "files" / "UK_Europe_Lead_List_FILLED.csv")
    from outbound_engine.lead_manager import import_from_csv
    result = import_from_csv(csv_path)
    return result


@app.post("/api/leads/{lead_id}/stage")
async def api_update_stage(lead_id: str, request: Request):
    body = await request.json()
    from outbound_engine.lead_manager import update_lead_stage
    success = update_lead_stage(lead_id, body.get("stage", ""), body.get("note", ""))
    return {"success": success}


@app.post("/api/leads/{lead_id}/note")
async def api_add_note(lead_id: str, request: Request):
    body = await request.json()
    from outbound_engine.lead_manager import add_note
    success = add_note(lead_id, body.get("note", ""))
    return {"success": success}


@app.get("/api/leads/stats/pipeline")
async def api_pipeline_stats():
    from outbound_engine.lead_manager import get_pipeline_stats
    return get_pipeline_stats()


# ═══════════════════════════════════════════════════════════════
#  EMAIL GENERATION API
# ═══════════════════════════════════════════════════════════════

@app.post("/api/emails/generate")
async def api_generate_email(request: Request):
    body = await request.json()
    lead_id = body.get("lead_id", "")
    email_type = body.get("email_type", "cold_outreach")

    from outbound_engine.lead_manager import get_lead
    from outbound_engine.email_generator import generate_email, score_email

    lead = get_lead(lead_id)
    if not lead:
        return JSONResponse(status_code=404, content={"error": "Lead not found"})

    email = generate_email(lead, email_type)
    quality = score_email(email)
    email["quality_score"] = quality

    return email


@app.post("/api/emails/generate-batch")
async def api_generate_batch(request: Request):
    body = await request.json()
    lead_ids = body.get("lead_ids", [])
    email_type = body.get("email_type", "cold_outreach")

    from outbound_engine.lead_manager import get_lead
    from outbound_engine.email_generator import generate_email, score_email

    emails = []
    for lid in lead_ids:
        lead = get_lead(lid)
        if lead:
            email = generate_email(lead, email_type)
            email["quality_score"] = score_email(email)
            emails.append(email)

    return {"emails": emails, "count": len(emails)}


@app.post("/api/emails/send")
async def api_send_campaign(request: Request):
    body = await request.json()
    emails = body.get("emails", [])
    schedule = body.get("schedule", "immediate")

    from outbound_engine.email_sender import send_campaign
    result = send_campaign(emails, schedule)
    return result


# ═══════════════════════════════════════════════════════════════
#  CAMPAIGN API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/campaigns")
async def api_get_campaigns():
    from outbound_engine.campaign_tracker import get_all_campaigns
    return {"campaigns": get_all_campaigns()}


@app.post("/api/campaigns")
async def api_create_campaign(request: Request):
    body = await request.json()
    from outbound_engine.campaign_tracker import create_campaign
    campaign = create_campaign(
        name=body.get("name", ""),
        email_type=body.get("email_type", "cold_outreach"),
        description=body.get("description", ""),
        target_countries=body.get("target_countries", []),
    )
    return campaign


@app.get("/api/campaigns/{campaign_id}/report")
async def api_campaign_report(campaign_id: str):
    from outbound_engine.campaign_tracker import get_campaign_report
    return get_campaign_report(campaign_id)


@app.get("/api/analytics")
async def api_analytics():
    from outbound_engine.campaign_tracker import get_overall_analytics, get_send_log_summary
    return {
        "campaigns": get_overall_analytics(),
        "send_logs": get_send_log_summary(7),
    }


# ═══════════════════════════════════════════════════════════════
#  PIPELINE API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/pipeline")
async def api_pipeline_view():
    from sales_pipeline import get_pipeline_view
    return get_pipeline_view()


@app.get("/api/pipeline/analytics")
async def api_pipeline_analytics():
    from sales_pipeline import get_pipeline_analytics
    return get_pipeline_analytics()


@app.get("/api/pipeline/forecast")
async def api_revenue_forecast():
    from sales_pipeline import get_revenue_forecast
    return get_revenue_forecast()


@app.post("/api/pipeline/deals")
async def api_create_deal(request: Request):
    body = await request.json()
    from sales_pipeline import create_deal
    deal = create_deal(
        lead_id=body.get("lead_id", ""),
        company_name=body.get("company_name", ""),
        contact_name=body.get("contact_name", ""),
        estimated_value=body.get("estimated_value", 0),
        product_category=body.get("product_category", ""),
    )
    return deal


@app.post("/api/pipeline/deals/{deal_id}/stage")
async def api_update_deal_stage(deal_id: str, request: Request):
    body = await request.json()
    from sales_pipeline import update_deal_stage
    success = update_deal_stage(deal_id, body.get("stage", ""), body.get("note", ""))
    return {"success": success}


# ═══════════════════════════════════════════════════════════════
#  LEAD SCORING API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/scoring")
async def api_score_all():
    from outbound_engine.lead_manager import get_all_leads
    from sales_pipeline.lead_scorer import score_all_leads, get_score_distribution
    leads = get_all_leads()
    return get_score_distribution(leads)


@app.get("/api/scoring/{lead_id}")
async def api_score_lead(lead_id: str):
    from outbound_engine.lead_manager import get_lead
    from sales_pipeline.lead_scorer import score_lead
    lead = get_lead(lead_id)
    if not lead:
        return JSONResponse(status_code=404, content={"error": "Lead not found"})
    return score_lead(lead)


# ═══════════════════════════════════════════════════════════════
#  CONTENT OPS API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/content/catalog")
async def api_catalog():
    from content_ops.catalog_generator import generate_catalog_markdown
    return {"content": generate_catalog_markdown(), "format": "markdown"}


@app.post("/api/content/catalog/save")
async def api_save_catalog(request: Request):
    body = await request.json()
    from content_ops.catalog_generator import save_catalog
    filepath = save_catalog(format=body.get("format", "markdown"))
    return {"filepath": filepath}


@app.get("/api/content/case-studies")
async def api_case_studies():
    from content_ops.case_study_generator import list_case_studies
    return {"case_studies": list_case_studies()}


@app.post("/api/content/case-studies")
async def api_create_case_study(request: Request):
    body = await request.json()
    from content_ops.case_study_generator import create_case_study, generate_case_study_markdown
    cs = create_case_study(
        client_name=body.get("client_name", ""),
        industry=body.get("industry", ""),
        country=body.get("country", ""),
        challenge=body.get("challenge", ""),
        solution=body.get("solution", ""),
        results=body.get("results", {}),
        testimonial=body.get("testimonial", ""),
        title=body.get("title", ""),
    )
    cs["markdown"] = generate_case_study_markdown(cs)
    return cs


@app.get("/api/content/calendar")
async def api_content_calendar(month: Optional[str] = None, quarter: Optional[int] = None):
    from content_ops.content_calendar import generate_monthly_calendar, generate_quarterly_calendar
    if quarter:
        return generate_quarterly_calendar(quarter)
    return generate_monthly_calendar(month)


@app.post("/api/content/score")
async def api_score_content(request: Request):
    body = await request.json()
    from content_ops.quality_scorer import score_content
    return score_content(
        content=body.get("content", ""),
        content_type=body.get("content_type", "email"),
    )


# ═══════════════════════════════════════════════════════════════
#  DEAL RESURRECTOR API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/resurrector")
async def api_cold_deals():
    from sales_pipeline.deal_resurrector import get_resurrection_report
    return get_resurrection_report()


# ═══════════════════════════════════════════════════════════════
#  HEALTH
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "Bassi Clothing AI Marketing Dashboard",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


# ─── Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    import os
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8000"))
    print(f"\n🚀 Bassi Clothing AI Marketing Dashboard")
    print(f"   http://{host}:{port}")
    print(f"   API docs: http://{host}:{port}/docs\n")
    uvicorn.run(app, host=host, port=port)
