import argparse
from .scanner import analyze_url
from .phishing_lab import analyze_email, create_awareness_demo
from .memory import save_result, history
from .authorized_lab import scan_private_host
from .web_nest import crawl_site, search_nests
from .recon import inspect_public_site
from .reports import write_report
from .web_audit import audit_page
from .vulnerability_hunter import run_assessment
from .injection_lab import audit_source_tree, export_local_sqlite
from .injection_training_lab import run_sql_injection_lab

def main():
    parser = argparse.ArgumentParser(
        prog="THE SPIDER OMEGA",
        description="Authorized security testing and phishing-awareness toolkit")
    sub = parser.add_subparsers(dest="command", required=True)
    p_url = sub.add_parser("scan-url", help="Analyze URL indicators locally; makes no network request")
    p_url.add_argument("url")
    p_mail = sub.add_parser("analyze-email", help="Analyze pasted email text")
    p_mail.add_argument("--text", required=True)
    p_demo = sub.add_parser("simulate", help="Create a safe awareness training page")
    p_demo.add_argument("--output", default="phishing_awareness_demo.html")
    p_hist = sub.add_parser("history", help="Show recent local scan history")
    p_hist.add_argument("--limit", type=int, default=20)
    p_lab = sub.add_parser('lab-scan', help='Limited TCP checks for private lab IPs only')
    p_lab.add_argument('host')
    p_lab.add_argument('--ports', default='22,80,443,8080')
    p_lab.add_argument('--i-own-this-lab', action='store_true')
    p_crawl = sub.add_parser("crawl-site", help="Explore public pages and build a local website nest")
    p_crawl.add_argument("url")
    p_crawl.add_argument("--pages", type=int, default=20)
    p_crawl.add_argument("--depth", type=int, default=2)
    p_crawl.add_argument("--keywords", default="")
    p_crawl.add_argument("--delay", type=float, default=2.0)
    p_crawl.add_argument("--i-have-permission", action="store_true")
    p_recon = sub.add_parser("recon", help="Passive DNS, HTTP header and TLS inspection")
    p_recon.add_argument("host")
    p_recon.add_argument("--report", default="recon")
    p_audit = sub.add_parser("web-audit", help="Run non-invasive checks on one website page")
    p_audit.add_argument("url")
    p_audit.add_argument("--report", default="web_audit")
    p_vuln = sub.add_parser("vuln-scan", help="Run defensive configuration and exposure checks")
    p_vuln.add_argument("url")
    p_vuln.add_argument("--report", default="vulnerability")
    p_sqli = sub.add_parser("sql-audit", help="Audit local Python source for risky SQL construction")
    p_sqli.add_argument("--path", default=".")
    p_sqli.add_argument("--report", default="sql_audit")
    p_export = sub.add_parser("db-export", help="Export tables from a local SQLite database")
    p_export.add_argument("database")
    p_export.add_argument("--output", default="omega_exports")
    p_injlab = sub.add_parser("injection-lab", help="Run a safe SQL injection demonstration in in-memory SQLite")
    p_search = sub.add_parser("nest-search", help="Search saved website nests")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.command == "scan-url":
        result = analyze_url(args.url)
        save_result("url", args.url, result["risk"], "; ".join(result["flags"]))
        print(f'Risk: {result["risk"]} | Score: {result["score"]}/100')
        print(f'Host: {result["host"]}')
        for flag in result["flags"]: print(f"- {flag}")
        if not result["flags"]: print("No heuristic indicators found; this does not prove the URL is safe.")
    elif args.command == "analyze-email":
        result = analyze_email(args.text)
        save_result("email", "pasted-text", result["risk"], "; ".join(result["flags"]))
        print(f'Risk: {result["risk"]}')
        for flag in result["flags"]: print(f"- {flag}")
        for item in result["urls"]:
            print(f'URL: {item["url"]} => {item["risk"]} ({item["score"]}/100)')
    elif args.command == "simulate":
        print("Created:", create_awareness_demo(args.output))
    elif args.command == "lab-scan":
        if not args.i_own_this_lab:
            parser.error("Confirm authorization with --i-own-this-lab.")
        try:
            results = scan_private_host(args.host, [int(x) for x in args.ports.split(",")])
        except ValueError as exc:
            parser.error(str(exc))
        for item in results:
            print("TCP/{}: {}".format(item["port"], item["status"]))
        opened = [str(x["port"]) for x in results if x["status"] == "open"]
        save_result("lab-tcp", args.host, "INFO", "Open ports: " + ", ".join(opened))
    elif args.command == "crawl-site":
        if not args.i_have_permission:
            parser.error("Confirm permission to crawl this website with --i-have-permission.")
        if not 1 <= args.pages <= 100 or not 0 <= args.depth <= 5:
            parser.error("--pages must be 1..100 and --depth 0..5.")
        try:
            result = crawl_site(args.url, args.pages, args.depth, args.keywords.split(","), args.delay)
        except ValueError as exc:
            parser.error(str(exc))
        print("Nest:", result["database"])
        print("Pages stored:", result["stored"])
        for note in result["notes"]: print("Note:", note)
        save_result("web-nest", result["seed"], "INFO", "Stored {} pages".format(result["stored"]))
    elif args.command == "recon":
        result = inspect_public_site(args.host)
        for key, value in result.items(): print("{}: {}".format(key, value))
        paths = write_report(result, args.report)
        print("Reports:", paths[0], paths[1])
        save_result("passive-recon", args.host, "INFO", "Report: " + paths[0])
    elif args.command == "web-audit":
        try:
            result = audit_page(args.url)
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
        print("Risk:", result.get("risk", "INFO"))
        for finding in result.get("findings", []):
            print("[{}] {}: {}".format(finding["severity"].upper(), finding["code"], finding["detail"]))
        paths = write_report(result, args.report)
        print("Reports:", paths[0], paths[1])
        save_result("web-audit", args.url, result.get("risk", "INFO"), "Report: " + paths[0])
    elif args.command == "vuln-scan":
        try:
            result = run_assessment(args.url)
        except ValueError as exc:
            parser.error(str(exc))
        print("Risk:", result["risk"])
        for finding in result["findings"]:
            print("[{}] {}: {}".format(finding["severity"].upper(), finding["id"], finding["detail"]))
        paths = write_report(result, args.report)
        print("Reports:", paths[0], paths[1])
        save_result("vulnerability-assessment", args.url, result["risk"], "Report: " + paths[0])
    elif args.command == "sql-audit":
        result = audit_source_tree(args.path)
        print("Files scanned:", result["files_scanned"])
        for finding in result["findings"]:
            print("[{}] {}:{} {}".format(finding["severity"].upper(), finding.get("file", ""), finding.get("line", 0), finding["rule"]))
        paths = write_report(result, args.report)
        print("Reports:", paths[0], paths[1])
        save_result("sql-source-audit", args.path, "INFO", "Findings: {}".format(len(result["findings"])))
    elif args.command == "db-export":
        try:
            result = export_local_sqlite(args.database, args.output)
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
        for table in result["tables_exported"]:
            print("{}: {} rows -> {}".format(table["table"], table["rows"], table["json"]))
        print("Tables exported:", len(result["tables_exported"]))
    elif args.command == "injection-lab":
        result = run_sql_injection_lab()
        print("Lab:", result["lab"])
        print("Test input:", result["test_input"])
        print("Vulnerable query returned:", result["vulnerable_query_count"], "rows")
        print("Parameterized query returned:", result["parameterized_query_count"], "rows")
        print("Lesson:", result["lesson"])
    elif args.command == "nest-search":
        rows = search_nests(args.query, args.limit)
        for title, url, excerpt, saved, keywords in rows:
            print("\\n{}\\n{}\\n{}\\nKeywords: {}".format(title or "(untitled)", url, excerpt, keywords))
        print("Results:", len(rows))
    elif args.command == "history":
        for row in history(max(1, args.limit)): print(" | ".join(map(str, row)))
    return 0
