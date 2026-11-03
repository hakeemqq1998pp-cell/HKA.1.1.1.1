"""Passive DNS, HTTP security-header and TLS inspection."""
import socket
import ssl
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SECURITY_HEADERS = (
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
)

def inspect_public_site(value):
    value = value if "://" in value else "https://" + value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("A valid HTTP(S) hostname is required.")
    host = parsed.hostname
    result = {"host": host, "dns": {}, "http": {}, "tls": {}}
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        result["dns"]["addresses"] = sorted({item[4][0] for item in records})
    except OSError as exc:
        result["dns"]["error"] = str(exc)
        return result
    try:
        request = Request(
            parsed.scheme + "://" + host + "/",
            headers={"User-Agent": "THE-SPIDER-OMEGA/1.0 (passive audit)"}
        )
        with urlopen(request, timeout=8) as response:
            headers = {key.lower(): val for key, val in response.headers.items()}
            result["http"] = {
                "status": response.status,
                "final_url": response.geturl(),
                "content_type": headers.get("content-type", ""),
                "security_headers": {
                    key: headers[key] for key in SECURITY_HEADERS if key in headers
                },
                "missing_security_headers": [
                    key for key in SECURITY_HEADERS if key not in headers
                ],
            }
    except Exception as exc:
        result["http"] = {"error": str(exc)[:240]}
    if parsed.scheme == "https":
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=5) as raw:
                with context.wrap_socket(raw, server_hostname=host) as conn:
                    cert = conn.getpeercert()
                    result["tls"] = {
                        "version": conn.version(),
                        "cipher": conn.cipher()[0] if conn.cipher() else None,
                        "not_after": cert.get("notAfter"),
                        "issuer": cert.get("issuer"),
                    }
        except Exception as exc:
            result["tls"] = {"error": str(exc)[:240]}
    return result
