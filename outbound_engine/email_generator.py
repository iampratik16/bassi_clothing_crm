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
- Max length: {guidelines.get('max_word_count', 400)} words
- AVOID: {', '.join(guidelines.get('avoid', []))}
- INCLUDE: {', '.join(guidelines.get('include', []))}

IMPORTANT RULES:
1. Always write in first person PLURAL ("we", "our", "us") as the team at {company.get('name', 'Bassi Clothing')}. Say "we are at Bassi Clothing" — NEVER say "I'm [Name] from Bassi Clothing" or use any personal name introduction.
2. Use specific numbers (MOQ, lead times, prices) — never be vague
3. Reference the prospect's brand/company specifically
4. Keep emails between 300-400 words — long enough to be complete, short enough to be readable
5. NEVER cut off mid-sentence. Every sentence MUST be complete. This is NON-NEGOTIABLE.
6. Never mention competitor names
7. Sound human, not robotic — no buzzwords or corporate jargon
8. Always include product recommendations as bullet points with proper spacing
9. The email MUST end with the mandatory closing paragraph (see below) — NEVER omit it
"""


EMAIL_TYPE_PROMPTS = {
    "cold_outreach": """Write a deeply personalized cold outreach email to {contact_name} at {company_name}.

=== TARGET COMPANY PROFILE ===
Company: {company_name}
Company Description: {about}
Country: {country}
Industry: {industry}
Employees: {employees}
Revenue: {revenue}
Founded: {founded}

=== OUR FULL PRODUCT CATALOG ===
{product_recommendations}

=== BASSI CLOTHING COMPANY DIFFERENTIATORS ===
Many brands face challenges with long lead times (6-8 weeks from the Far East), high MOQs, and inconsistent quality across batches. We solve all three:
- MOQ as low as 300 pieces per style
- 90-100 day production turnaround
- SEDEX 4 Pillar certified factory by SETMA, Zedd silver certification
- Direct manufacturer — no middlemen markup

CRITICAL PERSONALIZATION RULES:
1. You MUST read the Company Description above carefully and reference SPECIFIC details about their brand (e.g., their style, product categories, brand values, history, or target customers).
2. Based on the Company Description, identify which of our products are MOST RELEVANT to what this company sells. For example, if they sell streetwear, recommend hoodies and t-shirts. If they sell formal/smart-casual, recommend polo shirts. If they focus on sustainability, recommend organic products.
3. List 2-4 of our most relevant products as BULLET POINTS. Each bullet MUST be on its own line with a BLANK LINE between bullets. Each bullet should include: product name, MOQ, FOB price, and one key feature. Use this EXACT format:

• Product Name — MOQ X pieces, $X.XX-X.XX FOB, key feature here

• Next Product — MOQ X pieces, $X.XX-X.XX FOB, key feature here

• Third Product — MOQ X pieces, $X.XX-X.XX FOB, key feature here

4. If they focus on sustainability, highlight our GOTS/Oeko-Tex certifications and organic products.
5. If they are a luxury brand, emphasize our premium quality and custom capabilities.
6. If they are a streetwear/casual brand, emphasize our hoodies, t-shirts, and joggers.

MANDATORY EMAIL STRUCTURE (follow this order EXACTLY):

SECTION 1 — PERSONALIZED GREETING (1-2 sentences):
Open with "Hi {contact_name}," and a sentence referencing something specific about their brand from the Company Description.

SECTION 2 — INTRODUCTION + FIT (2-3 sentences):
Introduce using "we are at Bassi Clothing" (NOT "I'm [Name] from Bassi Clothing" — NEVER use personal name introductions). Explain why we are a great fit for their specific brand.

SECTION 3 — COMPANY DIFFERENTIATORS (include this paragraph):
Include a paragraph mentioning that many brands face challenges with long lead times, high MOQs, and inconsistent quality, and that we solve these with:
• MOQ as low as 300 pieces per style
• 90-100 day production turnaround
• SEDEX 4 Pillar certified factory by SETMA, Zedd silver certification
• Direct manufacturer — no middlemen markup

SECTION 4 — PRODUCT RECOMMENDATIONS (2-4 bullet points):
Based on what the company sells, recommend 2-4 relevant products from our catalog. Format each as a bullet point with product name, MOQ, price, and a key feature. Put a BLANK LINE between each bullet point.

SECTION 5 — MANDATORY CLOSING (copy this VERBATIM — do NOT change a single word):
We work with fashion retailers across the UK and EU, and I'd love to explore if we could be a reliable manufacturing partner for your upcoming collections.

Would a quick 15-minute call this week work to discuss your sourcing needs? I can also send over our catalog and samples — no commitment.

CRITICAL FORMATTING RULES:
- The email MUST be 300-400 words. Do NOT write less than 300 words.
- Write COMPLETE sentences — NEVER cut off mid-sentence. If you run out of space, finish the sentence.
- Put a blank line between each paragraph and between each bullet point.
- Use plain English. NO special characters, NO unicode symbols, NO emojis.
- Use only standard ASCII apostrophes (') and quotes (").
- Do NOT include any sign-off like "Best regards" or "Warm regards" — the email ends after the "no commitment" line.
- The last two paragraphs of the email MUST be the mandatory closing text above. This is NON-NEGOTIABLE.

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

    # Use only first name for personalization (e.g., "Emma Lindström" → "Emma")
    full_name = contact.get("name", "there") or "there"
    first_name = full_name.split()[0] if full_name and full_name != "there" else "there"

    # Build product recommendations based on the company's profile
    products = _load_products()
    about_text = lead.get("about", "") or ""
    industry_text = lead.get("industry", "") or ""
    profile_text = (about_text + " " + industry_text).lower()
    
    product_recs = []
    for p in products:
        relevance_keywords = (p.get("category", "") + " " + p.get("description", "")).lower()
        # Add all products but order by rough relevance
        product_recs.append(
            f"- {p['name']} ({p['category']}): ${p.get('price_range_usd', 'N/A')} FOB, "
            f"MOQ {p.get('moq', 'N/A')} pcs, {p.get('lead_time_days', 'N/A')}-day lead time, "
            f"Fabrics: {', '.join(p.get('fabrics', [])[:2])}, "
            f"Certifications: {', '.join(p.get('certifications', []))}"
        )
    product_recommendations = "\n".join(product_recs) if product_recs else "Full catalog available on request."

    context = {
        "company_name": lead.get("company_name", "your company"),
        "contact_name": first_name,
        "about": about_text[:800] if about_text else "No company details available — write a general but professional email.",
        "country": lead.get("country", "Europe"),
        "industry": lead.get("industry", "Fashion"),
        "employees": lead.get("employees", ""),
        "revenue": lead.get("revenue", ""),
        "founded": lead.get("founded", ""),
        "season": _get_season(),
        "product_recommendations": product_recommendations,
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

    # Mandatory closing text — always appended if missing
    MANDATORY_CLOSING = (
        "\n\nWe work with fashion retailers across the UK and EU, and I'd love to explore "
        "if we could be a reliable manufacturing partner for your upcoming collections."
        "\n\nWould a quick 15-minute call this week work to discuss your sourcing needs? "
        "I can also send over our catalog and samples — no commitment."
    )

    try:
        # Build the full prompt with system instructions + user request
        full_prompt = f"""{system_prompt}

---

{user_prompt}

IMPORTANT: You MUST respond with ONLY a valid JSON object. No markdown, no code fences, no extra text.
Use escaped newlines (\\n) inside string values. Example format:
{{"subject": "Subject line here", "body": "Line 1\\n\\nLine 2\\n\\nLine 3"}}"""

        # Disable thinking so all output tokens go to the actual email content
        # gemini-2.5-flash uses thinking by default, which consumes output tokens
        try:
            from google.genai import types
            gen_config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8192,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
        except (ImportError, AttributeError):
            gen_config = {
                "temperature": 0.7,
                "max_output_tokens": 8192,
            }

        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=gen_config,
        )

        content = response.text.strip()
        # Fix encoding: replace common unicode issues with ASCII equivalents
        content = content.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
        content = content.replace("\u2013", "-").replace("\u2014", "-").replace("\u2026", "...").replace("\u00a0", " ")
        content = content.replace("\xe2\x80\x99", "'").replace("\xe2\x80\x93", "-")

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

        # Post-processing: ensure the mandatory closing is always present
        body = result.get("body", "")
        if "no commitment" not in body.lower():
            # The mandatory closing was cut off — append it
            body = body.rstrip()
            # Clean up any incomplete sentence at the end
            if body and not body[-1] in '.!?:':
                # Find the last complete sentence
                last_period = max(body.rfind('.'), body.rfind('!'), body.rfind('?'))
                if last_period > len(body) * 0.5:  # Only trim if we'd keep at least half
                    body = body[:last_period + 1]
            body += MANDATORY_CLOSING
            result["body"] = body

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

• 90-100 day production turnaround

• SEDEX 4 Pillar certified factory by SETMA, Zedd silver certification

• Direct manufacturer — no middlemen markup

We work with fashion retailers across the UK and EU, and I'd love to explore if we could be a reliable manufacturing partner for your upcoming collections.

Would a quick 15-minute call this week work to discuss your sourcing needs? I can also send over our catalog and samples — no commitment.""",
        },
        "follow_up_case_study": {
            "subject": f"Quick case study — how a {context['country']} brand saved 30% on manufacturing",
            "body": f"""Hi {context['contact_name']},

Following up on my previous note. I wanted to share a quick result:

A mid-size {context['country']} fashion brand came to us with the same challenge most brands face — their Far East supplier was quoting 8-week lead times with MOQ 5,000+.

We delivered 2,000 GOTS-certified hoodies in 22 days at 30% lower cost. They've since placed repeat orders for their SS26 collection.

Would love to discuss how we could achieve similar results for {context['company_name']}. Shall I send over our portfolio?""",
        },
        "follow_up_samples": {
            "subject": f"Free samples for {context['company_name']} — no strings attached",
            "body": f"""Hi {context['contact_name']},

I know you're busy, so I'll keep this brief.

I'd like to send you free samples of our bestselling products — no commitment, no follow-up pressure. Just so you can see and feel the quality firsthand.

We can have samples at your door within 7 business days.

Interested? Just reply with your shipping address and which categories interest you (tees, hoodies, denim, activewear, or sustainable).""",
        },
        "breakup": {
            "subject": f"Should I close your file, {context['contact_name']}?",
            "body": f"""Hi {context['contact_name']},

I've reached out a few times and haven't heard back, which I completely understand — timing is everything in this business.

I don't want to be a bother, so I'll close your file for now.

If sourcing ever becomes a priority — whether it's exploring new manufacturing partners, needing lower MOQs, or faster turnaround — my inbox is always open.

Wishing {context['company_name']} continued success.""",
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
