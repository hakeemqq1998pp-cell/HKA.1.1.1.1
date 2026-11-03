from urllib.parse import urlparse
import ipaddress
import re

SUSPICIOUS_WORDS = {
    "login", "verify", "account", "secure", "update", "password",
    "wallet", "confirm", "signin", "bank", "bonus", "free"
}

def analyze_url(url: str) -> dict:
    raw = url.strip()
    parsed = urlparse(raw)
    flags = []
    if parsed.scheme not in ("http", "https"):
        flags.append("Unsupported or missing URL scheme")
    if parsed.scheme == "http":
        flags.append("Unencrypted HTTP connection")
    if parsed.username or parsed.password:
        flags.append("User information embedded in URL")
    host = parsed.hostname or ""
    try:
        ipaddress.ip_address(host)
        flags.append("URL uses a raw IP address instead of a domain")
    except ValueError:
        pass
    if host.startswith("xn--") or ".xn--" in host:
        flags.append("Punycode domain may conceal look-alike characters")
    if host.count(".") >= 4:
        flags.append("Unusually many subdomains")
    if len(raw) > 180:
        flags.append("Unusually long URL")
    lowered = (host + parsed.path + "?" + parsed.query).lower()
    matches = sorted(word for word in SUSPICIOUS_WORDS if re.search(r"[a-z0-9]", word) and word in lowered)
    if matches:
        flags.append("Sensitive-themed terms: " + ", ".join(matches))
    if not host:
        flags.append("No valid hostname found")
    score = min(100, len(flags) * 18)
    risk = "HIGH" if score >= 55 else "MEDIUM" if score >= 25 else "LOW"
    return {"url": raw, "host": host, "risk": risk, "score": score, "flags": flags}
