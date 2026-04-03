"""
Bassi Clothing — Deal Resurrector
===================================
Identify cold/stale deals and generate re-engagement strategies.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent.parent


def find_cold_deals(days_inactive: int = 30) -> List[Dict]:
    """Find deals with no activity for N+ days."""
    from sales_pipeline import get_all_deals

    deals = get_all_deals()
    cold_deals = []

    for deal in deals:
        if deal["stage"] in ("won", "lost"):
            continue

        last_activity = datetime.fromisoformat(deal.get("last_activity_at", deal["created_at"]))
        inactive_days = (datetime.now() - last_activity).days

        if inactive_days >= days_inactive:
            cold_deals.append({
                **deal,
                "days_inactive": inactive_days,
                "urgency": "critical" if inactive_days > 60 else "high" if inactive_days > 30 else "medium",
            })

    return sorted(cold_deals, key=lambda x: -x["days_inactive"])


def generate_reengagement_strategy(deal: Dict) -> Dict:
    """Generate a re-engagement strategy for a cold deal."""
    days = deal.get("days_inactive", 30)
    stage = deal.get("stage", "contacted")

    strategies = {
        "contacted": {
            "approach": "Value-first re-engagement",
            "actions": [
                "Send a relevant industry insight or trend report",
                "Share a case study from a similar company in their market",
                "Offer free samples with no commitment",
                "Mention a seasonal deadline they might be missing",
            ],
            "email_angle": "We recently worked with a brand similar to yours and achieved [specific result]. Thought you might find this relevant.",
            "urgency_hook": "With SS26 production windows closing soon, I wanted to reach out before it's too late for your planning cycle.",
        },
        "replied": {
            "approach": "Warmth + new value",
            "actions": [
                "Reference their previous reply and acknowledge the gap",
                "Share something new (new certification, expanded capability, pricing update)",
                "Offer a no-pressure video call to reconnect",
                "Send a physical sample box if address is known",
            ],
            "email_angle": "We spoke a while back and I wanted to share an update — we've recently [new achievement]. Would love to reconnect.",
            "urgency_hook": "We've just opened up additional production capacity for Q3/Q4 and I thought of your team.",
        },
        "meeting_booked": {
            "approach": "Direct follow-up",
            "actions": [
                "Acknowledge the dropped meeting without guilt-tripping",
                "Offer flexible rescheduling options",
                "Send a brief video introduction instead",
                "Connect on LinkedIn as a softer touchpoint",
            ],
            "email_angle": "I know schedules get hectic. Would it be easier to do a quick 10-minute call this week, or would you prefer I send over our catalog so you can review at your own pace?",
            "urgency_hook": "I have some time this week and would love to make it easy for you.",
        },
        "negotiation": {
            "approach": "High-value rescue",
            "actions": [
                "Address potential objections proactively",
                "Offer an improved term or sweetener",
                "Connect them with a reference client",
                "Propose a trial order at reduced risk",
            ],
            "email_angle": "I wanted to follow up on our conversation. If pricing/MOQs were the sticking point, we've recently been able to offer more flexibility for first orders.",
            "urgency_hook": "We're currently offering a trial order program — MOQ 200 at standard pricing — to remove risk for new partners.",
        },
    }

    strategy = strategies.get(stage, strategies["contacted"])

    return {
        "deal_id": deal.get("id", ""),
        "company_name": deal.get("company_name", ""),
        "days_inactive": days,
        "current_stage": stage,
        "urgency": deal.get("urgency", "medium"),
        **strategy,
        "recommended_timing": "Within 48 hours" if days > 60 else "This week",
        "follow_up_cadence": [
            "Day 1: Re-engagement email",
            "Day 3: LinkedIn connection/message",
            "Day 7: Value-add content (case study/samples offer)",
            "Day 14: Final check-in or breakup email",
        ],
    }


def get_resurrection_report() -> Dict:
    """Get a full report of deals that need attention."""
    cold_deals = find_cold_deals(days_inactive=14)

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_cold_deals": len(cold_deals),
        "by_urgency": {
            "critical": [d for d in cold_deals if d.get("urgency") == "critical"],
            "high": [d for d in cold_deals if d.get("urgency") == "high"],
            "medium": [d for d in cold_deals if d.get("urgency") == "medium"],
        },
        "total_at_risk_value": sum(d.get("estimated_value", 0) for d in cold_deals),
        "strategies": [],
    }

    for deal in cold_deals[:10]:  # Top 10 most urgent
        strategy = generate_reengagement_strategy(deal)
        report["strategies"].append(strategy)

    return report
