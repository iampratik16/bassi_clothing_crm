"""
Bassi Clothing — Campaign Tracker
==================================
Track campaign performance: opens, replies, bounces, conversions.
Generate performance reports and learning insights.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CAMPAIGNS_FILE = BASE_DIR / "data" / "campaigns.json"
SEND_LOG_DIR = BASE_DIR / "output" / "send_logs"


def _load_campaigns() -> List[Dict]:
    if CAMPAIGNS_FILE.exists():
        with open(CAMPAIGNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_campaigns(campaigns: List[Dict]):
    CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CAMPAIGNS_FILE, "w", encoding="utf-8") as f:
        json.dump(campaigns, f, indent=2, default=str)


def create_campaign(
    name: str,
    email_type: str,
    target_countries: List[str] = None,
    target_industries: List[str] = None,
    description: str = "",
) -> Dict:
    """Create a new campaign record."""
    campaigns = _load_campaigns()

    campaign = {
        "id": f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "name": name,
        "email_type": email_type,
        "description": description,
        "target_countries": target_countries or [],
        "target_industries": target_industries or [],
        "status": "draft",
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "stats": {
            "total_leads": 0,
            "emails_generated": 0,
            "emails_sent": 0,
            "emails_opened": 0,
            "replies": 0,
            "bounces": 0,
            "opt_outs": 0,
            "meetings_booked": 0,
        },
    }

    campaigns.append(campaign)
    _save_campaigns(campaigns)
    return campaign


def get_campaign(campaign_id: str) -> Optional[Dict]:
    for c in _load_campaigns():
        if c["id"] == campaign_id:
            return c
    return None


def get_all_campaigns() -> List[Dict]:
    return _load_campaigns()


def update_campaign_status(campaign_id: str, status: str) -> bool:
    campaigns = _load_campaigns()
    for c in campaigns:
        if c["id"] == campaign_id:
            c["status"] = status
            if status == "running":
                c["started_at"] = datetime.now().isoformat()
            elif status in ("completed", "paused"):
                c["completed_at"] = datetime.now().isoformat()
            _save_campaigns(campaigns)
            return True
    return False


def update_campaign_stats(campaign_id: str, stats_update: Dict) -> bool:
    """Update campaign statistics."""
    campaigns = _load_campaigns()
    for c in campaigns:
        if c["id"] == campaign_id:
            for key, value in stats_update.items():
                if key in c.get("stats", {}):
                    c["stats"][key] = value
            _save_campaigns(campaigns)
            return True
    return False


def record_reply(campaign_id: str, lead_id: str, reply_type: str = "positive") -> bool:
    """Record a reply to a campaign email."""
    campaigns = _load_campaigns()
    for c in campaigns:
        if c["id"] == campaign_id:
            c["stats"]["replies"] = c["stats"].get("replies", 0) + 1
            c.setdefault("replies_log", []).append({
                "lead_id": lead_id,
                "reply_type": reply_type,
                "timestamp": datetime.now().isoformat(),
            })
            _save_campaigns(campaigns)
            return True
    return False


def record_meeting(campaign_id: str, lead_id: str) -> bool:
    """Record a meeting booked from a campaign."""
    campaigns = _load_campaigns()
    for c in campaigns:
        if c["id"] == campaign_id:
            c["stats"]["meetings_booked"] = c["stats"].get("meetings_booked", 0) + 1
            c.setdefault("meetings_log", []).append({
                "lead_id": lead_id,
                "timestamp": datetime.now().isoformat(),
            })
            _save_campaigns(campaigns)
            return True
    return False


def get_campaign_report(campaign_id: str) -> Dict:
    """Generate a detailed campaign performance report."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        return {"error": "Campaign not found"}

    stats = campaign.get("stats", {})
    sent = max(stats.get("emails_sent", 0), 1)

    report = {
        "campaign": campaign["name"],
        "campaign_id": campaign_id,
        "status": campaign["status"],
        "email_type": campaign["email_type"],
        "created_at": campaign["created_at"],
        "stats": stats,
        "rates": {
            "open_rate": f"{(stats.get('emails_opened', 0) / sent * 100):.1f}%",
            "reply_rate": f"{(stats.get('replies', 0) / sent * 100):.1f}%",
            "bounce_rate": f"{(stats.get('bounces', 0) / sent * 100):.1f}%",
            "meeting_rate": f"{(stats.get('meetings_booked', 0) / sent * 100):.1f}%",
            "opt_out_rate": f"{(stats.get('opt_outs', 0) / sent * 100):.1f}%",
        },
        "benchmarks": {
            "open_rate": "40-50% (B2B average)",
            "reply_rate": "5-10% (B2B average)",
            "meeting_rate": "1-3% (B2B average)",
        },
    }

    return report


def get_overall_analytics() -> Dict:
    """Get analytics across all campaigns."""
    campaigns = _load_campaigns()

    total_sent = 0
    total_replies = 0
    total_meetings = 0
    total_bounces = 0
    total_optouts = 0

    by_type = {}

    for c in campaigns:
        stats = c.get("stats", {})
        sent = stats.get("emails_sent", 0)
        total_sent += sent
        total_replies += stats.get("replies", 0)
        total_meetings += stats.get("meetings_booked", 0)
        total_bounces += stats.get("bounces", 0)
        total_optouts += stats.get("opt_outs", 0)

        etype = c.get("email_type", "unknown")
        if etype not in by_type:
            by_type[etype] = {"sent": 0, "replies": 0, "meetings": 0}
        by_type[etype]["sent"] += sent
        by_type[etype]["replies"] += stats.get("replies", 0)
        by_type[etype]["meetings"] += stats.get("meetings_booked", 0)

    safe_sent = max(total_sent, 1)

    return {
        "total_campaigns": len(campaigns),
        "active_campaigns": sum(1 for c in campaigns if c["status"] == "running"),
        "total_emails_sent": total_sent,
        "total_replies": total_replies,
        "total_meetings": total_meetings,
        "total_bounces": total_bounces,
        "total_opt_outs": total_optouts,
        "overall_reply_rate": f"{(total_replies / safe_sent * 100):.1f}%",
        "overall_meeting_rate": f"{(total_meetings / safe_sent * 100):.1f}%",
        "by_email_type": by_type,
    }


def get_send_log_summary(days: int = 7) -> Dict:
    """Get send log summary for the last N days."""
    daily_stats = {}

    for i in range(days):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = SEND_LOG_DIR / f"{day}.json"

        day_stats = {"sent": 0, "dry_run": 0, "skipped": 0, "errors": 0, "bounced": 0}

        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)
                for log in logs:
                    status = log.get("status", "error")
                    day_stats[status] = day_stats.get(status, 0) + 1

        daily_stats[day] = day_stats

    return {
        "period": f"Last {days} days",
        "daily": daily_stats,
        "total_sent": sum(d["sent"] for d in daily_stats.values()),
        "total_dry_run": sum(d["dry_run"] for d in daily_stats.values()),
    }
