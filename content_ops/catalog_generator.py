"""
Bassi Clothing — Product Catalog Generator
============================================
Generate beautifully formatted product catalog content from the product database.
Supports Markdown and HTML output.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTS_FILE = BASE_DIR / "data" / "products.json"
OUTPUT_DIR = BASE_DIR / "output" / "catalogs"

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def _load_products() -> List[Dict]:
    if PRODUCTS_FILE.exists():
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("products", data) if isinstance(data, dict) else data
    return []


def _get_ai_client():
    if not HAS_OPENAI:
        return None
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-your"):
        return None
    return OpenAI(api_key=api_key)


def generate_product_description(product: Dict, style: str = "b2b") -> str:
    """Generate an AI-enhanced product description."""
    client = _get_ai_client()

    if client:
        try:
            prompt = f"""Write a compelling B2B product description for a garment manufacturer's catalog.

Product: {product.get('name', '')}
Category: {product.get('category', '')}
MOQ: {product.get('moq', '')} pieces
Lead Time: {product.get('lead_time_days', '')} days
Price Range: ${product.get('price_range_usd', '')} FOB
Fabrics: {', '.join(product.get('fabrics', []))}
Certifications: {', '.join(product.get('certifications', []))}
Customization: {', '.join(product.get('customization', []))}
Base Description: {product.get('description', '')}

Write a professional 80-word description that:
- Highlights quality and value for B2B buyers
- Mentions key specs (MOQ, lead time, certifications)
- Uses confident but not pushy tone
- Focuses on what matters to procurement teams

Return ONLY the description text, no headers or formatting."""

            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass

    # Fallback: template-based description
    fabrics = ", ".join(product.get("fabrics", [])[:3])
    certs = ", ".join(product.get("certifications", []))
    customs = ", ".join(product.get("customization", [])[:3])

    return (
        f"{product.get('description', product.get('name', 'Premium garment'))}. "
        f"Available in {fabrics}. "
        f"Certified: {certs}. "
        f"MOQ {product.get('moq', 'N/A')} pieces with {product.get('lead_time_days', 'N/A')}-day production. "
        f"Customization includes {customs}. "
        f"Price: ${product.get('price_range_usd', 'N/A')} FOB."
    )


def generate_catalog_markdown(
    title: str = "Bassi Clothing — Product Catalog 2026",
    products: List[Dict] = None,
) -> str:
    """Generate a full product catalog in Markdown format."""
    if products is None:
        products = _load_products()

    lines = [
        f"# {title}",
        "",
        f"*Generated: {datetime.now().strftime('%B %Y')}*",
        "",
        "---",
        "",
        "## Why Choose Bassi Clothing?",
        "",
        "- **Direct Manufacturer** — No middlemen, competitive pricing",
        "- **Low MOQs** — Starting from just 300 pieces per style",
        "- **Fast Turnaround** — 20-30 days from approval to delivery",
        "- **Certified Quality** — GOTS, Oeko-Tex, GRS certified",
        "- **EU/UK Ready** — Established export infrastructure",
        "- **Free Samples** — Within 7 business days, no commitment",
        "",
        "---",
        "",
    ]

    # Group by category
    categories = {}
    for p in products:
        cat = p.get("category", "Other")
        categories.setdefault(cat, []).append(p)

    for cat_name, cat_products in categories.items():
        lines.append(f"## {cat_name}")
        lines.append("")

        for product in cat_products:
            lines.append(f"### {product.get('name', 'Product')}")
            lines.append("")
            lines.append(f"**SKU:** {product.get('id', 'N/A')}")
            lines.append("")

            desc = generate_product_description(product)
            lines.append(desc)
            lines.append("")

            lines.append("| Spec | Detail |")
            lines.append("|------|--------|")
            lines.append(f"| **MOQ** | {product.get('moq', 'N/A')} pieces |")
            lines.append(f"| **Lead Time** | {product.get('lead_time_days', 'N/A')} days |")
            lines.append(f"| **FOB Price** | ${product.get('price_range_usd', 'N/A')} |")
            lines.append(f"| **Fabrics** | {', '.join(product.get('fabrics', []))} |")
            lines.append(f"| **Certifications** | {', '.join(product.get('certifications', []))} |")
            lines.append(f"| **Sizes** | {', '.join(product.get('sizes', [])) if isinstance(product.get('sizes'), list) else product.get('sizes', 'N/A')} |")
            lines.append(f"| **Customization** | {', '.join(product.get('customization', []))} |")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.extend([
        "## Get Started",
        "",
        "Ready to discuss your next collection?",
        "",
        "- 📧 Email: sourcing@bassiclothing.com",
        "- 📞 Contact us for a free consultation",
        "- 📦 Request free samples — delivered in 7 days",
        "",
        "*All prices are FOB. Shipping to EU/UK arranged on request.*",
        "",
    ])

    return "\n".join(lines)


def generate_catalog_html(title: str = "Bassi Clothing — Product Catalog 2026") -> str:
    """Generate a styled HTML catalog."""
    products = _load_products()
    md_content = generate_catalog_markdown(title, products)

    # Simple markdown to HTML conversion
    html_body = md_content
    import re
    # Headers
    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
    # Bold
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    # Italic
    html_body = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_body)
    # List items
    html_body = re.sub(r'^- (.+)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)
    # HR
    html_body = html_body.replace("---", "<hr/>")
    # Paragraphs
    html_body = re.sub(r'\n\n', '</p><p>', html_body)
    html_body = f"<p>{html_body}</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>{title}</title>
<style>
  body {{ font-family: 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto;
         padding: 40px 20px; color: #1a1a2e; line-height: 1.7; background: #fafafa; }}
  h1 {{ color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 12px; }}
  h2 {{ color: #0f3460; margin-top: 40px; }}
  h3 {{ color: #533483; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
  th, td {{ padding: 10px 14px; border: 1px solid #ddd; text-align: left; }}
  th {{ background: #0f3460; color: white; }}
  tr:nth-child(even) {{ background: #f5f5f5; }}
  hr {{ border: none; border-top: 2px solid #e0e0e0; margin: 30px 0; }}
  li {{ margin: 4px 0; }}
  strong {{ color: #0f3460; }}
</style>
</head>
<body>{html_body}</body>
</html>"""


def save_catalog(format: str = "markdown") -> str:
    """Generate and save catalog to output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")

    if format == "html":
        content = generate_catalog_html()
        filepath = OUTPUT_DIR / f"bassi_catalog_{timestamp}.html"
    else:
        content = generate_catalog_markdown()
        filepath = OUTPUT_DIR / f"bassi_catalog_{timestamp}.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return str(filepath)
