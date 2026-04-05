"""
Bassi Clothing — AI Email Generator (Gemini Pro)
==================================================
Generate personalized B2B cold emails using Google Gemini Pro.
Supports multiple email types: cold outreach, follow-ups, case study shares, breakup emails.
"""

import json
import os
import yaml
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "bassi_config.yaml"
CASE_STUDIES_FILE = BASE_DIR / "data" / "case_studies.json"
PRODUCTS_FILE = BASE_DIR / "data" / "products.json"
OUTPUT_DIR = BASE_DIR / "output" / "emails"

# Load environment
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env", override=True)


# Try to import Google GenAI
try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def _load_config() -> Dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_case_studies() -> List[Dict]:
    if CASE_STUDIES_FILE.exists():
        with open(CASE_STUDIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _load_products() -> List[Dict]:
    if PRODUCTS_FILE.exists():
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("products", data) if isinstance(data, dict) else data
    return []


def _get_gemini_client() -> Optional[object]:
    """Initialize Google Gemini client."""
    if not HAS_GEMINI:
        return None
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key or api_key.startswith("your"):
        return None
    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception:
        return None


def _get_season() -> str:
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "Spring/Summer"
    elif month in [6, 7, 8]:
        return "Summer/Autumn"
    elif month in [9, 10, 11]:
        return "Autumn/Winter"
    return "Winter/Spring"


def _build_system_prompt(config: Dict) -> str:
    """Build the LLM system prompt from Bassi config."""
    company = config.get("company", {})
    vp = config.get("value_proposition", {})
    guidelines = config.get("content_guidelines", {})
    products = _load_products()

    product_summary = "\n".join(
        f"  - {p['category']}: MOQ {p.get('moq', 'N/A')}, "
        f"Lead time {p.get('lead_time_days', 'N/A')} days, "
        f"Price {p.get('price_range_usd', 'N/A')} USD FOB"
        for p in products[:6]
    )

    case_studies = _load_case_studies()
    cs_summary = "\n".join(
        f"  - {cs['title']}: {cs['results'].get('cost_savings', 'N/A')} cost savings, "
        f"{cs['results'].get('delivery', 'N/A')}"
        for cs in case_studies[:3]
    )

    return f"""You are an expert B2B email copywriter for {company.get('name', 'Bassi Clothing')}.
Industry: {company.get('industry', 'B2B Garment Manufacturing & Export')}
Target market: {company.get('target_market', 'UK and European Fashion Retailers')}

VALUE PROPOSITION:
{vp.get('main_message', '')}

KEY BENEFITS:
{chr(10).join('  - ' + b for b in vp.get('key_benefits', []))}

DIFFERENTIATORS:
{chr(10).join('  - ' + d for d in vp.get('differentiators', []))}

PAIN POINTS WE SOLVE:
{chr(10).join('  - ' + p for p in vp.get('pain_points_addressed', []))}

PRODUCTS:
{product_summary}

CASE STUDIES:
{cs_summary}

WRITING GUIDELINES:
- Tone: {guidelines.get('tone', 'Professional but approachable')}
- Max length: {guidelines.get('max_word_count', 180)} words
- AVOID: {', '.join(guidelines.get('avoid', []))}
- INCLUDE: {', '.join(guidelines.get('include', []))}

IMPORTANT RULES:
1. Always write in first person as a representative of {company.get('name', 'Bassi Clothing')}
2. Use specific numbers (MOQ, lead times, prices) — never be vague
3. Reference the prospect's brand/company specifically
4. Keep emails under {guidelines.get('max_word_count', 180)} words
5. End with a clear, low-pressure CTA (samples, catalog, 15-min call)
6. Never mention competitor names
7. Sound human, not robotic — no buzzwords or corporate jargon
"""


EMAIL_TYPE_PROMPTS = {
    "cold_outreach": """Write a personalized cold outreach email to {contact_name} at {company_name}.
Company info: {about}
Country: {country}
Industry: {industry}
Employees: {employees}

This is our FIRST email to them. Make it:
- Personalized (reference something specific about their brand)
- Problem-aware (mention a pain point relevant to their business)
- Solution-oriented (briefly mention how we solve it)
- Low-friction CTA (offer samples, catalog, or a quick 15-min call)

Return a JSON object with:
{{"subject": "email subject line", "body": "email body text (plain text, no HTML)"}}""",

    "follow_up_case_study": """Write a follow-up email to {contact_name} at {company_name}.
We sent them a cold email a few days ago and haven't heard back.
Company info: {about}
Country: {country}

This email should:
- Briefly reference the previous email (don't repeat it)
- Share a relevant case study or portfolio piece as social proof
- Keep it shorter than the first email (under 120 words)
- Include a specific number or result to build credibility

Return a JSON object with:
{{"subject": "email subject line", "body": "email body text (plain text, no HTML)"}}""",

    "follow_up_samples": """Write a 3rd touchpoint email to {contact_name} at {company_name}.
We've emailed twice with no response.
Company info: {about}
Country: {country}

This email should:
- Acknowledge they're busy
- Offer something tangible: FREE samples with no commitment
- Mention specific products relevant to their brand
- Keep it very short (under 100 words)
- Make it easy to say yes

Return a JSON object with:
{{"subject": "email subject line", "body": "email body text (plain text, no HTML)"}}""",

    "breakup": """Write a "breakup" email to {contact_name} at {company_name}.
This is our 4th and final email — they haven't responded to 3 previous emails.
Company info: {about}
Country: {country}

This email should:
- Be very brief (under 80 words)
- Politely ask permission to close their file
- Leave the door open for future contact
- Use mild reverse psychology ("if now's not the right time...")
- Include your email for when they're ready

Return a JSON object with:
{{"subject": "email subject line", "body": "email body text (plain text, no HTML)"}}""",
}


def generate_email(
    lead: Dict,
    email_type: str = "cold_outreach",
    custom_prompt: str = "",
    generation_method: str = "ai",
) -> Dict:
    """
    Generate a personalized email for a lead using Gemini Pro.
    Falls back to template-based generation if Gemini is unavailable.
    """
    config = _load_config()
    contact = {}
    if lead.get("contacts"):
        contact = lead["contacts"][0]

    context = {
        "company_name": lead.get("company_name", "your company"),
        "contact_name": contact.get("name", "there") or "there",
        "about": lead.get("about", "")[:500],
        "country": lead.get("country", "Europe"),
        "industry": lead.get("industry", "Fashion"),
        "employees": lead.get("employees", ""),
        "season": _get_season(),
    }

    if generation_method == "template":
        return _generate_from_template(config, context, email_type)

    client = _get_gemini_client()
    if not client:
        fallback = _generate_from_template(config, context, email_type)
        fallback["error"] = "Gemini API key is not configured or invalid."
        return fallback

    result = _generate_with_gemini(client, config, context, email_type, custom_prompt)
    if result.get("error"):
        fallback = _generate_from_template(config, context, email_type)
        fallback["error"] = result["error"]
        return fallback

    return result


def _generate_with_gemini(
    client, config: Dict, context: Dict, email_type: str, custom_prompt: str
) -> Dict:
    """Generate email using Google Gemini Pro."""
    system_prompt = _build_system_prompt(config)

    if custom_prompt:
        user_prompt = custom_prompt.format(**context)
    elif email_type in EMAIL_TYPE_PROMPTS:
        user_prompt = EMAIL_TYPE_PROMPTS[email_type].format(**context)
    else:
        user_prompt = EMAIL_TYPE_PROMPTS["cold_outreach"].format(**context)

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    try:
        # Build the full prompt with system instructions + user request
        full_prompt = f"""{system_prompt}

---

{user_prompt}

IMPORTANT: You MUST respond with ONLY a valid JSON object. No markdown, no code fences, no extra text.
Use escaped newlines (\\n) inside string values. Example format:
{{"subject": "Subject line here", "body": "Line 1\\n\\nLine 2\\n\\nLine 3"}}"""

        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config={
                "temperature": 0.7,
                "max_output_tokens": 1200,
            },
        )

        content = response.text.strip()

        # Clean up response — remove markdown code fences if present
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

        # Try parsing with fixes for common AI JSON mistakes
        def try_parse(text):
            text = text.replace("\\'", "'")
            try:
                return json.loads(text)
            except Exception as e:
                # If it's truncated, try appending closing braces/quotes
                if "Unterminated string" in str(e) or "Expecting ',' delimiter" in str(e) or "Expecting property name" in str(e):
                    for suffix in ['"}', '"}', '}']:
                        try:
                            return json.loads(text + suffix)
                        except:
                            pass
                
                # Try replacing raw newlines with \\n
                text_no_nl = text.replace("\n", "\\n")
                try:
                    return json.loads(text_no_nl)
                except:
                    pass
                
                raise e

        try:
            result = try_parse(content)
        except Exception:
            # Absolute last resort: regex
            subj_match = re.search(r'"subject"\s*:\s*"([^"]*)"', content, re.DOTALL)
            body_match = re.search(r'"body"\s*:\s*"([\s\S]*?)("?\s*\}|$)', content, re.DOTALL)
            
            if subj_match:
                body_text = body_match.group(1).strip() if body_match else ""
                
                # Fix unicode escapes (e.g. \u2019 -> ')
                try:
                    body_text = body_text.encode('utf-8').decode('unicode_escape')
                except Exception:
                    pass
                    
                body_text = body_text.replace('\\n', '\n').replace('\\"', '"')
                
                subj_text = subj_match.group(1).strip()
                try:
                    subj_text = subj_text.encode('utf-8').decode('unicode_escape')
                except Exception:
                    pass
                    
                result = {"subject": subj_text, "body": body_text}
            else:
                result = None

        if not result:
            raise ValueError(f"Could not parse Gemini response as JSON: {content[:300]}")

        return {
            "subject": result.get("subject", ""),
            "body": result.get("body", ""),
            "email_type": email_type,
            "model": model,
            "generated_at": datetime.now().isoformat(),
            "company_name": context["company_name"],
            "contact_name": context["contact_name"],
            "ai_generated": True,
            "tokens_used": 0,
        }
    except Exception as e:
        return {
            "error": f"Gemini API Error: {str(e)}",
            "email_type": email_type,
            "ai_generated": False,
        }


def _generate_from_template(config: Dict, context: Dict, email_type: str) -> Dict:
    """Fallback: generate email from templates when AI is unavailable."""
    company = config.get("company", {})
    vp = config.get("value_proposition", {})
    products = config.get("product_categories", [])

    templates = {
        "cold_outreach": {
            "subject": f"{context['company_name']} × {company.get('name', 'Bassi Clothing')} — Reliable Garment Manufacturing for {context['country']}",
            "body": f"""Hi {context['contact_name']},

I came across {context['company_name']} and was impressed by your brand's approach to fashion in the {context['country']} market.

Many brands like yours face challenges with long lead times (6-8 weeks from the Far East), high MOQs, and inconsistent quality across batches. We solve all three:

• MOQ as low as 300 pieces per style
• 20-30 day production turnaround
• GOTS & Oeko-Tex certified manufacturing
• Direct manufacturer — no middlemen markup

We work with fashion retailers across the UK and EU, and I'd love to explore if we could be a reliable manufacturing partner for your upcoming collections.

Would a quick 15-minute call this week work to discuss your sourcing needs? I can also send over our catalog and samples — no commitment.

Best regards,
{company.get('name', 'Bassi Clothing')} Team""",
        },
        "follow_up_case_study": {
            "subject": f"Quick case study — how a {context['country']} brand saved 30% on manufacturing",
            "body": f"""Hi {context['contact_name']},

Following up on my previous note. I wanted to share a quick result:

A mid-size {context['country']} fashion brand came to us with the same challenge most brands face — their Far East supplier was quoting 8-week lead times with MOQ 5,000+.

We delivered 2,000 GOTS-certified hoodies in 22 days at 30% lower cost. They've since placed repeat orders for their SS26 collection.

Would love to discuss how we could achieve similar results for {context['company_name']}. Shall I send over our portfolio?

Best,
{company.get('name', 'Bassi Clothing')} Team""",
        },
        "follow_up_samples": {
            "subject": f"Free samples for {context['company_name']} — no strings attached",
            "body": f"""Hi {context['contact_name']},

I know you're busy, so I'll keep this brief.

I'd like to send you free samples of our bestselling products — no commitment, no follow-up pressure. Just so you can see and feel the quality firsthand.

We can have samples at your door within 7 business days.

Interested? Just reply with your shipping address and which categories interest you (tees, hoodies, denim, activewear, or sustainable).

Cheers,
{company.get('name', 'Bassi Clothing')} Team""",
        },
        "breakup": {
            "subject": f"Should I close your file, {context['contact_name']}?",
            "body": f"""Hi {context['contact_name']},

I've reached out a few times and haven't heard back, which I completely understand — timing is everything in this business.

I don't want to be a bother, so I'll close your file for now.

If sourcing ever becomes a priority — whether it's exploring new manufacturing partners, needing lower MOQs, or faster turnaround — my inbox is always open.

Wishing {context['company_name']} continued success.

Best,
{company.get('name', 'Bassi Clothing')} Team""",
        },
    }

    template = templates.get(email_type, templates["cold_outreach"])

    return {
        "subject": template["subject"],
        "body": template["body"],
        "email_type": email_type,
        "model": "template",
        "generated_at": datetime.now().isoformat(),
        "company_name": context["company_name"],
        "contact_name": context["contact_name"],
        "ai_generated": False,
        "tokens_used": 0,
    }


def generate_campaign_emails(
    leads: List[Dict],
    email_type: str = "cold_outreach",
    campaign_id: str = "",
) -> List[Dict]:
    """Generate emails for a list of leads."""
    if not campaign_id:
        campaign_id = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    emails = []
    for i, lead in enumerate(leads):
        print(f"  [{i+1}/{len(leads)}] Generating email for {lead.get('company_name', 'Unknown')}...")
        email = generate_email(lead, email_type)
        email["campaign_id"] = campaign_id
        email["lead_id"] = lead.get("id", "")
        emails.append(email)

    # Save generated emails
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{campaign_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Generated {len(emails)} emails → {output_file}")
    return emails


def score_email(email: Dict) -> Dict:
    """Score an email on quality metrics."""
    body = email.get("body", "")
    subject = email.get("subject", "")
    scores = {}

    # Length score (ideal: 100-180 words)
    word_count = len(body.split())
    if 100 <= word_count <= 180:
        scores["length"] = 100
    elif 80 <= word_count <= 200:
        scores["length"] = 80
    elif word_count < 50 or word_count > 300:
        scores["length"] = 40
    else:
        scores["length"] = 60

    # Personalization score
    company_name = email.get("company_name", "")
    contact_name = email.get("contact_name", "")
    personalization = 0
    if company_name and company_name.lower() in body.lower():
        personalization += 40
    if contact_name and contact_name.lower() != "there" and contact_name.lower() in body.lower():
        personalization += 30
    if any(num in body for num in ["300", "20", "30%", "7 days", "MOQ"]):
        personalization += 30
    scores["personalization"] = min(personalization, 100)

    # CTA score
    cta_phrases = ["call", "samples", "catalog", "reply", "interested", "discuss", "schedule"]
    has_cta = any(phrase in body.lower() for phrase in cta_phrases)
    scores["cta_clarity"] = 100 if has_cta else 30

    # Subject line score
    subject_len = len(subject)
    if 30 <= subject_len <= 60:
        scores["subject_line"] = 100
    elif 20 <= subject_len <= 80:
        scores["subject_line"] = 70
    else:
        scores["subject_line"] = 40

    # Overall score
    weights = {"length": 0.25, "personalization": 0.35, "cta_clarity": 0.20, "subject_line": 0.20}
    overall = sum(scores[k] * weights[k] for k in weights)
    scores["overall"] = round(overall, 1)

    return scores
