import re
from urllib.parse import urlparse
from .scanner import analyze_url

URGENT_TERMS = ("urgent", "immediately", "suspended", "verify", "password",
                "payment", "account locked", "action required")

def analyze_email(text: str) -> dict:
    lowered = text.lower()
    flags = []
    hits = [term for term in URGENT_TERMS if term in lowered]
    if hits:
        flags.append("Urgency or credential-pressure language: " + ", ".join(hits))
    if re.search(r"\b(dear customer|dear user|valued customer)\b", lowered):
        flags.append("Generic greeting")
    urls = re.findall(r"https?://[^\s<>\"']+", text, flags=re.I)
    url_results = [analyze_url(u.rstrip(".,);")) for u in urls]
    if urls:
        flags.append(f"Contains {len(urls)} URL(s); inspect destinations carefully")
    risk = "HIGH" if any(x["risk"] == "HIGH" for x in url_results) or len(flags) >= 3 else (
        "MEDIUM" if flags else "LOW")
    return {"risk": risk, "flags": flags, "urls": url_results}

def create_awareness_demo(output_path: str = "phishing_awareness_demo.html") -> str:
    # Safe training page: no login form, no credential collection, no external requests.
    html = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>Security Awareness Exercise</title>
<style>body{font:17px system-ui;max-width:720px;margin:10vh auto;padding:24px;background:#101018;color:#eee}
main{border:1px solid #a020f0;border-radius:14px;padding:28px}h1{color:#ff4040}</style>
<main><h1>Training simulation</h1>
<p>This is a safe phishing-awareness exercise. No password or personal information was requested or stored.</p>
<h2>Warning signs to check</h2><ul><li>Unexpected urgency</li><li>Unfamiliar sender or domain</li>
<li>Links whose destination differs from their displayed text</li><li>Requests for passwords or payment</li></ul>
<p>Always navigate to important services using a known bookmark or official app.</p></main></html>"""
    from pathlib import Path
    path = Path(output_path)
    path.write_text(html, encoding="utf-8")
    return str(path)
