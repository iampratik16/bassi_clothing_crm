"""
Bassi Clothing — Apollo Lead Search
=====================================
Search Apollo.io for leads matching the ICP defined in bassi_config.yaml.
Exports results as Excel file for the dashboard.
"""

import json
import os
import time
import yaml
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "bassi_config.yaml"
OUTPUT_DIR = BASE_DIR / "output" / "apollo"

# Load environment
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

APOLLO_API_BASE = "https://api.apollo.io/api/v1"


def _load_config() -> Dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_api_key() -> str:
    return os.environ.get("APOLLO_API_KEY", "")


def _build_search_params(config: Dict) -> Dict:
    """Build Apollo API search parameters from ICP config."""
    icp = config.get("ideal_customer_profile", {})

    # Map locations to Apollo format
    location_map = {
        "United Kingdom": "United Kingdom",
        "France": "France",
        "Germany": "Germany",
        "Netherlands": "Netherlands",
        "Italy": "Italy",
        "Spain": "Spain",
        "Sweden": "Sweden",
        "Denmark": "Denmark",
        "Belgium": "Belgium",
        "Ireland": "Ireland",
    }

    locations = []
    for loc in icp.get("locations", []):
        mapped = location_map.get(loc, loc)
        locations.append(mapped)

    # Decision maker titles
    titles = icp.get("decision_makers", [])

    # Company size
    size = icp.get("company_size", {})
    min_emp = size.get("min_employees", 50)
    max_emp = size.get("max_employees", 10000)

    # Build employee range string for Apollo
    # Apollo uses ranges like "51,200", "201,500", etc.
    employee_ranges = []
    if min_emp <= 50:
        employee_ranges.extend(["11,20", "21,50", "51,100", "101,200", "201,500", "501,1000", "1001,2000", "2001,5000", "5001,10000"])
    elif min_emp <= 100:
        employee_ranges.extend(["51,100", "101,200", "201,500", "501,1000", "1001,2000", "2001,5000", "5001,10000"])
    else:
        employee_ranges.extend(["101,200", "201,500", "501,1000", "1001,2000", "2001,5000", "5001,10000"])

    # Industry keywords from company types
    keywords = icp.get("company_types", [])

    params = {
        "person_titles": titles,
        "organization_locations": locations,
        "organization_num_employees_ranges": employee_ranges,
        "q_organization_keyword_tags": keywords,
        "page": 1,
        "per_page": 100,
    }

    return params


def _extract_domain(url: str) -> str:
    """Extract clean domain from a URL string."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "http://" + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "").strip("/")
        return domain
    except Exception:
        return ""


def _enrich_organization(domain: str, api_key: str) -> Dict:
    """
    Enrich a single organization via Apollo's enrichment endpoint
    to get the full company description.
    """
    if not domain or not api_key:
        return {}

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key,
    }

    try:
        response = requests.get(
            f"{APOLLO_API_BASE}/organizations/enrich",
            headers=headers,
            params={"domain": domain},
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            org = data.get("organization", {})
            if org:
                return org
    except Exception as e:
        print(f"  ⚠️ Enrichment failed for {domain}: {e}")

    return {}


def _get_about_from_org(org: Dict) -> str:
    """Extract the best available description from an org dict, trying all known field names."""
    for field in ["short_description", "seo_description", "description", "snippet", "tagline"]:
        val = org.get(field, "") or ""
        val = str(val).strip()
        if val and len(val) > 10:  # ignore trivially short texts
            return val
    return ""


def search_apollo_leads(
    page: int = 1, 
    per_page: int = 100, 
    location_override: str = "", 
    keywords_override: str = ""
) -> Dict:
    """
    Search Apollo for leads matching ICP from bassi_config.yaml.
    Uses the organizations/search endpoint.
    Returns search results with partial person/org data.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "Apollo API key not configured in .env", "leads": []}

    config = _load_config()
    params = _build_search_params(config)
    
    if location_override:
        params["organization_locations"] = [loc.strip() for loc in location_override.split(",") if loc.strip()]
        
    if keywords_override:
        params["q_organization_keyword_tags"] = [kw.strip() for kw in keywords_override.split(",") if kw.strip()]
        
    params["page"] = page
    params["per_page"] = per_page

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key,
    }

    try:
        response = requests.post(
            f"{APOLLO_API_BASE}/mixed_people/search",
            headers=headers,
            json=params,
            timeout=30,
        )

        if response.status_code == 422:
            # Try the newer endpoint
            response = requests.post(
                f"{APOLLO_API_BASE}/mixed_people/api_search",
                headers=headers,
                json=params,
                timeout=30,
            )

        if response.status_code == 403 and "API_INACCESSIBLE" in response.text:
            # Fallback to organizations search for free API plans
            params.pop("person_titles", None)
            response = requests.post(
                f"{APOLLO_API_BASE}/organizations/search",
                headers=headers,
                json=params,
                timeout=30,
            )

        if response.status_code != 200:
            return {
                "error": f"Apollo API returned {response.status_code}: {response.text[:500]}",
                "leads": [],
            }

        data = response.json()
        people = data.get("people", [])
        organizations = data.get("organizations", [])
        total = data.get("pagination", {}).get("total_entries", 0)

        # Parse results into our lead format
        leads = []
        seen_companies = set()

        # Handle people response
        for person in people:
            org = person.get("organization", {}) or {}
            company_name = org.get("name", "") or person.get("organization_name", "")

            if not company_name or company_name.lower() in seen_companies:
                continue
            seen_companies.add(company_name.lower())

            website_url = org.get("website_url", "") or ""
            about_text = _get_about_from_org(org)

            # If description is missing, enrich via the dedicated endpoint
            if not about_text and website_url:
                domain = _extract_domain(website_url)
                if domain:
                    print(f"  🔍 Enriching {company_name} ({domain}) for company description...")
                    enriched = _enrich_organization(domain, api_key)
                    if enriched:
                        about_text = _get_about_from_org(enriched)
                        # Also backfill any other missing fields from enrichment
                        if not org.get("phone") and enriched.get("phone"):
                            org["phone"] = enriched["phone"]
                        if not org.get("founded_year") and enriched.get("founded_year"):
                            org["founded_year"] = enriched["founded_year"]
                        if not org.get("annual_revenue") and enriched.get("annual_revenue"):
                            org["annual_revenue"] = enriched["annual_revenue"]
                    time.sleep(0.3)  # Rate limit protection

            lead = {
                "company_name": company_name,
                "person": person.get("name", ""),
                "email": "",  # Free tier doesn't return emails
                "primary_designation": person.get("title", ""),
                "website": website_url,
                "about": about_text,
                "company_phone": org.get("phone", "") or "",
                "company_linkedin": org.get("linkedin_url", "") or "",
                "industry": org.get("industry", "") or "",
                "employees": org.get("estimated_num_employees", "") or "",
                "revenue": "",
                "founded": org.get("founded_year", "") or "",
                "country": org.get("country", "") or person.get("country", "") or "",
                "primary_phone": person.get("phone_number", "") or "",
                "primary_linkedin": person.get("linkedin_url", "") or "",
            }

            # Try to get revenue from raw cents
            if org.get("annual_revenue"):
                rev = org["annual_revenue"]
                if isinstance(rev, (int, float)) and rev > 0:
                    if rev >= 1_000_000_000:
                        lead["revenue"] = f"${rev/1_000_000_000:.1f}B"
                    elif rev >= 1_000_000:
                        lead["revenue"] = f"${rev/1_000_000:.1f}M"
                    else:
                        lead["revenue"] = f"${rev/1_000:.0f}K"

            leads.append(lead)

        # Handle organizations response (fallback)
        for org in organizations:
            company_name = org.get("name", "")
            if not company_name or company_name.lower() in seen_companies:
                continue
            seen_companies.add(company_name.lower())

            website_url = org.get("website_url", "") or ""
            about_text = _get_about_from_org(org)

            # If description is missing, enrich via the dedicated endpoint
            if not about_text and website_url:
                domain = _extract_domain(website_url)
                if domain:
                    print(f"  🔍 Enriching {company_name} ({domain}) for company description...")
                    enriched = _enrich_organization(domain, api_key)
                    if enriched:
                        about_text = _get_about_from_org(enriched)
                        if not org.get("phone") and enriched.get("phone"):
                            org["phone"] = enriched["phone"]
                        if not org.get("founded_year") and enriched.get("founded_year"):
                            org["founded_year"] = enriched["founded_year"]
                        if not org.get("annual_revenue") and enriched.get("annual_revenue"):
                            org["annual_revenue"] = enriched["annual_revenue"]
                    time.sleep(0.3)  # Rate limit protection

            lead = {
                "company_name": company_name,
                "person": "",  # Missing in org search
                "email": "", 
                "primary_designation": "", # Missing in org search
                "website": website_url,
                "about": about_text,
                "company_phone": org.get("phone", "") or "",
                "company_linkedin": org.get("linkedin_url", "") or "",
                "industry": org.get("industry", "") or "",
                "employees": org.get("estimated_num_employees", "") or "",
                "revenue": "",
                "founded": org.get("founded_year", "") or "",
                "country": org.get("country", "") or "",
                "primary_phone": "",
                "primary_linkedin": "",
            }

            if org.get("annual_revenue"):
                rev = org["annual_revenue"]
                if isinstance(rev, (int, float)) and rev > 0:
                    if rev >= 1_000_000_000:
                        lead["revenue"] = f"${rev/1_000_000_000:.1f}B"
                    elif rev >= 1_000_000:
                        lead["revenue"] = f"${rev/1_000_000:.1f}M"
                    else:
                        lead["revenue"] = f"${rev/1_000:.0f}K"

            leads.append(lead)

        return {
            "leads": leads,
            "total": total,
            "page": page,
            "per_page": per_page,
            "search_params": {
                "locations": params.get("organization_locations", []),
                "titles": params.get("person_titles", []),
            },
        }

    except requests.exceptions.Timeout:
        return {"error": "Apollo API request timed out", "leads": []}
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to Apollo API", "leads": []}
    except Exception as e:
        return {"error": f"Apollo search failed: {str(e)}", "leads": []}


def export_leads_to_excel(leads: List[Dict], filename: str = "") -> str:
    """Export Apollo leads to Excel file matching UK_Europe_Lead_List_FILLED.csv format."""
    try:
        import pandas as pd
    except ImportError:
        return ""

    if not filename:
        filename = f"apollo_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename

    # Map to the expected CSV column format
    rows = []
    for lead in leads:
        rows.append({
            "Company Name": lead.get("company_name", ""),
            "Person": lead.get("person", ""),
            "Email": lead.get("email", ""),  # Will be empty — user fills manually
            "Primary_Designation": lead.get("primary_designation", ""),
            "Alternate_Person_Name": "",
            "Alternate_Email": "",
            "Alternate_Designation": "",
            "Website": lead.get("website", ""),
            "About": lead.get("about", ""),
            "Company_Phone": lead.get("company_phone", ""),
            "Company_LinkedIn": lead.get("company_linkedin", ""),
            "Industry": lead.get("industry", ""),
            "Employees": lead.get("employees", ""),
            "Revenue": lead.get("revenue", ""),
            "Founded": lead.get("founded", ""),
            "Country": lead.get("country", ""),
            "Primary_Phone": lead.get("primary_phone", ""),
            "Primary_LinkedIn": lead.get("primary_linkedin", ""),
            "Alternate2_Name": "",
            "Alternate2_Email": "",
            "Alternate2_Title": "",
        })

    df = pd.DataFrame(rows)
    df.to_excel(str(filepath), index=False, engine="openpyxl")

    return str(filepath)


def get_latest_export() -> Optional[str]:
    """Get the most recent Apollo export file path based on creation time."""
    if not OUTPUT_DIR.exists():
        return None

    exports = list(OUTPUT_DIR.glob("apollo_leads_*.xlsx"))
    if not exports:
        return None
        
    # Sort by actual OS modification time rather than string alphabetization
    import os
    exports.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return str(exports[0])
