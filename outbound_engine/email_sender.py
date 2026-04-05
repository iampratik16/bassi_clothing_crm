"""
Bassi Clothing — Email Sender
=============================
SMTP email sending with rate limiting, scheduling, GDPR unsubscribe links,
retry logic, and send tracking.
"""

import json
import os
import smtplib
import time
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SEND_LOG_DIR = BASE_DIR / "output" / "send_logs"

# SMTP Configuration
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_NAME = os.environ.get("SENDER_NAME", "Bassi Clothing")

# Safety settings
MAX_EMAILS_PER_DAY = int(os.environ.get("MAX_EMAILS_PER_DAY", "30"))
EMAIL_DELAY_SECONDS = int(os.environ.get("EMAIL_DELAY_SECONDS", "60"))
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

# Open tracking
TRACKING_BASE_URL = os.environ.get("TRACKING_BASE_URL", "http://127.0.0.1:8000")


UNSUBSCRIBE_HTML = """
<br/><br/>
<hr style="border:none;border-top:1px solid #e0e0e0;margin:24px 0"/>
<p style="font-size:11px;color:#888;line-height:1.6;">
  You received this email because we believe our garment manufacturing services
  may be relevant to your business. If you'd prefer not to hear from us,
  <a href="mailto:{sender_email}?subject=Unsubscribe&body=Please%20remove%20me%20from%20your%20mailing%20list." style="color:#888;">
    click here to unsubscribe
  </a>.
  <br/>
  {company_name} | {company_address}
</p>
"""

EMAIL_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
             font-size:14px;line-height:1.7;color:#333;max-width:600px;margin:0 auto;padding:20px;">
{body_html}
{unsubscribe}
{tracking_pixel}
</body>
</html>
"""


def _text_to_html(text: str) -> str:
    """Convert plain text email body to simple HTML."""
    import re
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Convert bullet points
    text = re.sub(r'^[•\-]\s*(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    # Wrap lists
    text = re.sub(r'((?:<li>.*?</li>\n?)+)', r'<ul style="padding-left:20px;margin:8px 0;">\1</ul>', text)
    # Convert paragraphs
    paragraphs = text.split("\n\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if p:
            if p.startswith("<ul") or p.startswith("<li"):
                html_parts.append(p)
            else:
                p = p.replace("\n", "<br/>")
                html_parts.append(f"<p style='margin:0 0 12px 0;'>{p}</p>")
    return "\n".join(html_parts)


def _build_html_email(body_text: str, send_id: str = "") -> str:
    """Build full HTML email with unsubscribe footer and tracking pixel."""
    body_html = _text_to_html(body_text)
    unsubscribe = UNSUBSCRIBE_HTML.format(
        sender_email=SENDER_EMAIL,
        company_name=SENDER_NAME,
        company_address="Bassi Clothing Manufacturing",
    )
    tracking_pixel = ""
    if send_id:
        pixel_url = f"{TRACKING_BASE_URL}/track/open/{send_id}"
        tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="" />'
    return EMAIL_HTML_TEMPLATE.format(
        body_html=body_html, unsubscribe=unsubscribe, tracking_pixel=tracking_pixel
    )


def _get_today_send_count() -> int:
    """Count emails sent today."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = SEND_LOG_DIR / f"{today}.json"
    if log_file.exists():
        with open(log_file, "r") as f:
            logs = json.load(f)
            return len([l for l in logs if l.get("status") == "sent"])
    return 0


def _log_send(email_data: Dict, status: str, error: str = ""):
    """Log an email send attempt."""
    SEND_LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = SEND_LOG_DIR / f"{today}.json"

    logs = []
    if log_file.exists():
        with open(log_file, "r") as f:
            logs = json.load(f)

    logs.append({
        "timestamp": datetime.now().isoformat(),
        "send_id": email_data.get("send_id", ""),
        "to_email": email_data.get("to_email", ""),
        "to_name": email_data.get("contact_name", ""),
        "company": email_data.get("company_name", ""),
        "subject": email_data.get("subject", ""),
        "email_type": email_data.get("email_type", ""),
        "campaign_id": email_data.get("campaign_id", ""),
        "status": status,
        "error": error,
        "dry_run": DRY_RUN,
        "is_bulk": email_data.get("is_bulk", False),
    })

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
    email_data: Dict = None,
) -> Dict:
    """
    Send a single email via SMTP.
    In DRY_RUN mode, logs the email but doesn't actually send.
    """
    if not email_data:
        email_data = {}

    # Generate a unique send_id for open tracking
    send_id = str(uuid.uuid4())
    email_data.update({
        "to_email": to_email,
        "contact_name": to_name,
        "subject": subject,
        "send_id": send_id,
    })

    # Check daily limit
    today_count = _get_today_send_count()
    if today_count >= MAX_EMAILS_PER_DAY:
        _log_send(email_data, "skipped", "Daily limit reached")
        return {
            "status": "skipped",
            "reason": f"Daily limit reached ({MAX_EMAILS_PER_DAY})",
            "sent_today": today_count,
        }

    # Check opted out
    from outbound_engine.lead_manager import is_opted_out
    if is_opted_out(to_email):
        _log_send(email_data, "skipped", "Opted out")
        return {"status": "skipped", "reason": "Contact has opted out (GDPR)"}

    # Build email with tracking pixel
    html_body = _build_html_email(body, send_id=send_id)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
    msg["Reply-To"] = SENDER_EMAIL
    msg["List-Unsubscribe"] = f"<mailto:{SENDER_EMAIL}?subject=Unsubscribe>"

    # Attach both plain text and HTML versions
    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    if DRY_RUN:
        _log_send(email_data, "dry_run")
        return {
            "status": "dry_run",
            "message": f"[DRY RUN] Would send to {to_email}",
            "subject": subject,
            "body_preview": body[:200],
        }

    # Actually send
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            _log_send(email_data, "error", "SMTP credentials not configured")
            return {"status": "error", "reason": "SMTP credentials not configured in .env"}

        if SMTP_PORT == 465:
            # SSL connection (GoDaddy / secureserver.net)
            import ssl
            context = ssl.create_default_context()
            # GoDaddy uses self-signed certs in chain — relax verification
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        else:
            # STARTTLS connection (Gmail, etc.)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())

        _log_send(email_data, "sent")
        return {
            "status": "sent",
            "message": f"Email sent to {to_email}",
            "subject": subject,
        }

    except smtplib.SMTPAuthenticationError:
        _log_send(email_data, "error", "SMTP authentication failed")
        return {"status": "error", "reason": "SMTP authentication failed. Check credentials."}
    except smtplib.SMTPRecipientsRefused:
        _log_send(email_data, "bounced", f"Recipient refused: {to_email}")
        return {"status": "bounced", "reason": f"Email address rejected: {to_email}"}
    except Exception as e:
        _log_send(email_data, "error", str(e))
        return {"status": "error", "reason": str(e)}


def send_campaign(
    emails: List[Dict],
    schedule: str = "immediate",
) -> Dict:
    """
    Send a batch of campaign emails.
    schedule: 'immediate' or 'staggered' (delay between each)
    """
    results = {"sent": 0, "dry_run": 0, "skipped": 0, "errors": 0, "details": []}

    for i, email in enumerate(emails):
        to_email = ""
        to_name = email.get("contact_name", "")

        # Find the email address from the lead data
        lead_id = email.get("lead_id", "")
        if lead_id:
            from outbound_engine.lead_manager import get_lead, record_campaign
            lead = get_lead(lead_id)
            if lead and lead.get("contacts"):
                for contact in lead["contacts"]:
                    if contact.get("email"):
                        to_email = contact["email"]
                        to_name = contact.get("name", to_name)
                        break

        if not to_email:
            results["skipped"] += 1
            results["details"].append({
                "company": email.get("company_name", "Unknown"),
                "status": "skipped",
                "reason": "No email address found",
            })
            continue

        print(f"  [{i+1}/{len(emails)}] Sending to {email.get('company_name', '')} ({to_email})...")

        result = send_email(
            to_email=to_email,
            to_name=to_name,
            subject=email.get("subject", ""),
            body=email.get("body", ""),
            email_data=email,
        )

        status = result.get("status", "error")
        results[status] = results.get(status, 0) + 1
        results["details"].append({
            "company": email.get("company_name", "Unknown"),
            "email": to_email,
            **result,
        })

        # Record campaign in lead manager
        if lead_id and status in ("sent", "dry_run"):
            try:
                record_campaign(lead_id, email.get("campaign_id", ""), email.get("email_type", ""))
            except Exception:
                pass

        # Staggered delay
        if schedule == "staggered" and i < len(emails) - 1:
            print(f"    ⏳ Waiting {EMAIL_DELAY_SECONDS}s before next email...")
            time.sleep(EMAIL_DELAY_SECONDS)

    print(f"\n📊 Campaign Results:")
    print(f"   ✅ Sent: {results.get('sent', 0)}")
    print(f"   🔍 Dry Run: {results.get('dry_run', 0)}")
    print(f"   ⏭️  Skipped: {results.get('skipped', 0)}")
    print(f"   ❌ Errors: {results.get('errors', 0)}")

    return results


def get_send_history(days: int = 7) -> List[Dict]:
    """Get send history for the last N days."""
    history = []
    for i in range(days):
        from datetime import timedelta
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = SEND_LOG_DIR / f"{day}.json"
        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)
                history.extend(logs)
    return history
