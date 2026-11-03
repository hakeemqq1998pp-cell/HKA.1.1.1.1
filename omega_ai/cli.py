"""Command-line interface for OMEGA AI CORE."""
import argparse
from .core import ask, status, OmegaAIError


def main():
    parser = argparse.ArgumentParser(prog="OMEGA AI CORE")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show local engine configuration")
    chat = sub.add_parser("ask", help="Send a prompt to the local model")
    chat.add_argument("prompt")
    chat.add_argument("--model")
    args = parser.parse_args()

    if args.command == "status":
        for key, value in status().items():
            print(f"{key}: {value}")
        return 0

    try:
        print(ask(args.prompt, model=args.model))
    except (OmegaAIError, ValueError) as exc:
        parser.error(str(exc))
    return 0
