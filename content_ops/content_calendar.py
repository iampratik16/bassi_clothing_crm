"""
Bassi Clothing — Content Calendar Generator
=============================================
Generate monthly content calendars for B2B marketing.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# Pre-built content ideas by month/season
CONTENT_IDEAS = {
    "January": [
        {"type": "LinkedIn Post", "topic": "New Year manufacturing capacity announcement", "goal": "Awareness"},
        {"type": "Email Newsletter", "topic": "SS26 Collection — Last call for production slots", "goal": "Lead Gen"},
        {"type": "Case Study", "topic": "End-of-year success story with UK client", "goal": "Trust"},
        {"type": "Blog Post", "topic": "5 Things EU Brands Should Look for in a Manufacturing Partner", "goal": "SEO"},
    ],
    "February": [
        {"type": "LinkedIn Post", "topic": "Behind-the-scenes: Factory tour + quality control", "goal": "Trust"},
        {"type": "Email Campaign", "topic": "Valentine's Day — Show Your Supply Chain Some Love", "goal": "Engagement"},
        {"type": "Whitepaper", "topic": "The True Cost of Changing Manufacturers (and How to Minimize It)", "goal": "Lead Gen"},
        {"type": "LinkedIn Post", "topic": "Sustainability certifications update", "goal": "Credibility"},
    ],
    "March": [
        {"type": "Email Campaign", "topic": "AW26 Production Windows — Early Bird Slots", "goal": "Lead Gen"},
        {"type": "LinkedIn Post", "topic": "Team spotlight: Our quality control process", "goal": "Trust"},
        {"type": "Blog Post", "topic": "Understanding MOQs: What UK Brands Need to Know", "goal": "SEO"},
        {"type": "LinkedIn Post", "topic": "Trade show preview — attending Pure London?", "goal": "Networking"},
    ],
    "April": [
        {"type": "LinkedIn Post", "topic": "Spring packaging innovations", "goal": "Awareness"},
        {"type": "Email Campaign", "topic": "AW26 Collection Planning — Free Consultation", "goal": "Lead Gen"},
        {"type": "Case Study", "topic": "How a German brand scaled from 500 to 10,000 units/month", "goal": "Trust"},
        {"type": "Blog Post", "topic": "Sustainable Manufacturing: GOTS vs Oeko-Tex Explained", "goal": "SEO"},
    ],
    "May": [
        {"type": "LinkedIn Post", "topic": "New fabric collection showcase", "goal": "Awareness"},
        {"type": "Email Campaign", "topic": "Q3 production slots — limited availability", "goal": "Urgency"},
        {"type": "LinkedIn Post", "topic": "Client testimonial spotlight", "goal": "Trust"},
        {"type": "Video", "topic": "Factory walkthrough: From fabric to finished garment", "goal": "Trust"},
    ],
    "June": [
        {"type": "Email Campaign", "topic": "Mid-year capacity update for EU/UK partners", "goal": "Lead Gen"},
        {"type": "LinkedIn Post", "topic": "Première Vision Paris — key trends we spotted", "goal": "Thought Leadership"},
        {"type": "Blog Post", "topic": "How to Reduce Lead Times Without Sacrificing Quality", "goal": "SEO"},
        {"type": "LinkedIn Post", "topic": "Celebrating 6 months of on-time deliveries", "goal": "Trust"},
    ],
    "July": [
        {"type": "Email Campaign", "topic": "SS27 early bird production — beat the rush", "goal": "Lead Gen"},
        {"type": "LinkedIn Post", "topic": "Summer shutdown? Not us — we produce year-round", "goal": "Differentiation"},
        {"type": "Case Study", "topic": "Activewear brand partnership in Netherlands", "goal": "Trust"},
        {"type": "Blog Post", "topic": "The Complete Guide to Private Label Manufacturing", "goal": "SEO"},
    ],
    "August": [
        {"type": "LinkedIn Post", "topic": "New season color palette preview", "goal": "Awareness"},
        {"type": "Email Campaign", "topic": "Back-to-business: Q4 production planning", "goal": "Lead Gen"},
        {"type": "LinkedIn Post", "topic": "Sustainability milestone: X tons of CO2 saved", "goal": "CSR"},
        {"type": "Blog Post", "topic": "UK Fashion Import Guide: Tariffs, Standards, and Logistics", "goal": "SEO"},
    ],
    "September": [
        {"type": "Email Campaign", "topic": "Pure London recap + SS27 readiness", "goal": "Lead Gen"},
        {"type": "LinkedIn Post", "topic": "Autumn collection shipping to EU partners", "goal": "Proof"},
        {"type": "Blog Post", "topic": "How Emerging Brands Can Compete on Quality Without Breaking the Bank", "goal": "SEO"},
        {"type": "LinkedIn Post", "topic": "Meet the team: Head of Quality Assurance", "goal": "Trust"},
    ],
    "October": [
        {"type": "Email Campaign", "topic": "SS27 production windows — planning for spring", "goal": "Lead Gen"},
        {"type": "LinkedIn Post", "topic": "Oeko-Tex certification renewed", "goal": "Credibility"},
        {"type": "Case Study", "topic": "Sustainable fashion startup — from concept to shelf", "goal": "Trust"},
        {"type": "Blog Post", "topic": "5 Questions to Ask Before Choosing a Garment Manufacturer", "goal": "SEO"},
    ],
    "November": [
        {"type": "Email Campaign", "topic": "End of year capacity + priority Q1 slots", "goal": "Urgency"},
        {"type": "LinkedIn Post", "topic": "Black Friday? Our focus is on quality, not fast fashion", "goal": "Brand"},
        {"type": "LinkedIn Post", "topic": "Year in review — partnerships, production, progress", "goal": "Trust"},
        {"type": "Blog Post", "topic": "Planning Your 2027 Fashion Collection: A Manufacturing Timeline", "goal": "SEO"},
    ],
    "December": [
        {"type": "LinkedIn Post", "topic": "Thank you to all our EU/UK partners — year in review", "goal": "Relationship"},
        {"type": "Email Campaign", "topic": "2027 Partnership Opportunities — Book a January Call", "goal": "Lead Gen"},
        {"type": "Blog Post", "topic": "Fashion Manufacturing Trends to Watch in 2027", "goal": "Thought Leadership"},
        {"type": "LinkedIn Post", "topic": "Holiday message + production restart date", "goal": "Communication"},
    ],
}


def generate_monthly_calendar(month: str = None, year: int = None) -> Dict:
    """Generate a content calendar for a specific month."""
    if not month:
        month = datetime.now().strftime("%B")
    if not year:
        year = datetime.now().year

    ideas = CONTENT_IDEAS.get(month, CONTENT_IDEAS.get("January"))

    calendar = {
        "month": month,
        "year": year,
        "generated_at": datetime.now().isoformat(),
        "content_items": [],
    }

    # Distribute across the month
    for i, idea in enumerate(ideas):
        week = i + 1
        item = {
            "week": week,
            "estimated_date": f"Week {week} of {month}",
            "content_type": idea["type"],
            "topic": idea["topic"],
            "goal": idea["goal"],
            "status": "planned",
            "notes": "",
        }
        calendar["content_items"].append(item)

    return calendar


def generate_quarterly_calendar(quarter: int = None) -> Dict:
    """Generate a 3-month content calendar."""
    if quarter is None:
        quarter = (datetime.now().month - 1) // 3 + 1

    months_map = {
        1: ["January", "February", "March"],
        2: ["April", "May", "June"],
        3: ["July", "August", "September"],
        4: ["October", "November", "December"],
    }

    months = months_map.get(quarter, months_map[1])
    year = datetime.now().year

    return {
        "quarter": f"Q{quarter} {year}",
        "months": [generate_monthly_calendar(m, year) for m in months],
        "total_items": sum(
            len(generate_monthly_calendar(m, year)["content_items"])
            for m in months
        ),
    }


def export_calendar_markdown(calendar: Dict) -> str:
    """Export calendar as Markdown."""
    lines = [
        f"# Content Calendar — {calendar.get('month', calendar.get('quarter', ''))} {calendar.get('year', '')}",
        "",
        f"*Generated: {datetime.now().strftime('%d %B %Y')}*",
        "",
    ]

    if "months" in calendar:
        for month_cal in calendar["months"]:
            lines.append(f"## {month_cal['month']}")
            lines.append("")
            lines.append("| Week | Type | Topic | Goal | Status |")
            lines.append("|------|------|-------|------|--------|")
            for item in month_cal["content_items"]:
                lines.append(
                    f"| {item['week']} | {item['content_type']} | "
                    f"{item['topic']} | {item['goal']} | {item['status']} |"
                )
            lines.append("")
    else:
        lines.append("| Week | Type | Topic | Goal | Status |")
        lines.append("|------|------|-------|------|--------|")
        for item in calendar.get("content_items", []):
            lines.append(
                f"| {item['week']} | {item['content_type']} | "
                f"{item['topic']} | {item['goal']} | {item['status']} |"
            )

    return "\n".join(lines)
