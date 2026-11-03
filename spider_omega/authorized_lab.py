"""Restricted TCP connect checks for explicitly authorized private lab hosts."""
import ipaddress
import socket

DEFAULT_PORTS = (22, 80, 443, 445, 3306, 5432, 8000, 8080, 8443)

def scan_private_host(host: str, ports=DEFAULT_PORTS, timeout=0.4):
    try:
        ip = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("Use a literal private or loopback IP address.") from exc
    if not (ip.is_private or ip.is_loopback):
        raise ValueError("Public IP addresses are blocked.")
    ports = tuple(dict.fromkeys(int(p) for p in ports))
    if len(ports) > 20 or any(p < 1 or p > 65535 for p in ports):
        raise ValueError("At most 20 valid TCP ports are allowed.")
    results = []
    for port in ports:
        sock = socket.socket(socket.AF_INET if ip.version == 4 else socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(max(0.1, min(float(timeout), 1.0)))
        try:
            status = "open" if sock.connect_ex((str(ip), port)) == 0 else "closed_or_filtered"
        finally:
            sock.close()
        results.append({"port": port, "status": status})
    return results
