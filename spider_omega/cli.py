import argparse
from .scanner import analyze_url
from .phishing_lab import analyze_email, create_awareness_demo
from .memory import save_result, history
from .authorized_lab import scan_private_host

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
    elif args.command == "history":
        for row in history(max(1, args.limit)): print(" | ".join(map(str, row)))
    return 0
