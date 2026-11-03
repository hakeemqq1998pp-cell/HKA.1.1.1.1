import argparse
from .scanner import analyze_url
from .phishing_lab import analyze_email, create_awareness_demo
from .memory import save_result, history
from .authorized_lab import scan_private_host
from .web_nest import crawl_site, search_nests

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
    elif args.command == "nest-search":
        rows = search_nests(args.query, args.limit)
        for title, url, excerpt, saved, keywords in rows:
            print("\\n{}\\n{}\\n{}\\nKeywords: {}".format(title or "(untitled)", url, excerpt, keywords))
        print("Results:", len(rows))
    elif args.command == "history":
        for row in history(max(1, args.limit)): print(" | ".join(map(str, row)))
    return 0
