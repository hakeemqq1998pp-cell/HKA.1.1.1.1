"""Non-invasive website security checks for a single page."""
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

class PageSignals(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.resources = []
        self._form = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "form":
            self._form = {"action": attrs.get("action", ""), "method": attrs.get("method", "get").lower()}
            self.forms.append(self._form)
        elif tag.lower() in ("script", "img", "iframe", "link"):
            key = "href" if tag.lower() == "link" else "src"
            if attrs.get(key):
                self.resources.append(attrs[key])

    def handle_endtag(self, tag):
        if tag.lower() == "form":
            self._form = None

def audit_page(value):
    value = value if "://" in value else "https://" + value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("A valid HTTP(S) URL is required.")
    request = Request(value, headers={"User-Agent": "THE-SPIDER-OMEGA/1.0 (defensive audit)"})
    with urlopen(request, timeout=10) as response:
        final_url = response.geturl()
        final = urlparse(final_url)
        if final.scheme not in ("http", "https"):
            raise ValueError("Unexpected redirect scheme.")
        raw = response.read(512 * 1024)
        content_type = response.headers.get("Content-Type", "")
        headers = {k.lower(): v for k, v in response.headers.items()}
        status = response.status
    if "html" not in content_type.lower():
        return {"url": value, "final_url": final_url, "status": status,
                "findings": [], "note": "Response is not HTML; page checks skipped."}
    parser = PageSignals()
    parser.feed(raw.decode("utf-8", errors="replace"))
    findings = []
    def add(severity, code, detail):
        findings.append({"severity": severity, "code": code, "detail": detail})
    if final.scheme != "https":
        add("high", "PAGE_NOT_HTTPS", "The page is served over HTTP.")
    cookies = response.headers.get_all("Set-Cookie") or []
    for cookie in cookies:
        lower = cookie.lower()
        if final.scheme == "https" and "secure" not in lower:
            add("medium", "COOKIE_MISSING_SECURE", "A Set-Cookie response lacks the Secure attribute.")
        if "httponly" not in lower:
            add("medium", "COOKIE_MISSING_HTTPONLY", "A Set-Cookie response lacks the HttpOnly attribute.")
        if "samesite" not in lower:
            add("low", "COOKIE_MISSING_SAMESITE", "A Set-Cookie response lacks the SameSite attribute.")
    for form in parser.forms:
        action = urljoin(final_url, form["action"] or final_url)
        action_url = urlparse(action)
        if final.scheme == "https" and action_url.scheme == "http":
            add("high", "FORM_DOWNGRADES_TO_HTTP", "A form submits to an HTTP endpoint.")
        if form["method"] == "get":
            add("info", "GET_FORM", "A form uses GET; verify it does not submit sensitive data.")
    for resource in parser.resources:
        target = urlparse(urljoin(final_url, resource))
        if final.scheme == "https" and target.scheme == "http":
            add("medium", "MIXED_CONTENT", "An embedded resource is loaded over HTTP.")
            break
    for header in ("content-security-policy", "x-content-type-options", "referrer-policy"):
        if header not in headers:
            add("low", "MISSING_" + header.upper().replace("-", "_"), "Recommended response header is absent: " + header)
    rank = {"info": 0, "low": 1, "medium": 2, "high": 3}
    highest = max((rank[x["severity"]] for x in findings), default=0)
    risk = {0: "INFO", 1: "LOW", 2: "MEDIUM", 3: "HIGH"}[highest]
    return {"url": value, "final_url": final_url, "status": status,
            "forms_found": len(parser.forms), "cookies_found": len(cookies),
            "findings": findings, "risk": risk,
            "note": "Non-invasive checks only; findings require manual validation."}
