"""Timestamped JSON and Markdown report exports."""
import json
from pathlib import Path
from datetime import datetime, timezone

def write_report(data, name="omega_report"):
    folder = Path("omega_reports")
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = folder / (name + "_" + stamp)
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    rendered = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    json_path.write_text(rendered, encoding="utf-8")
    markdown = (
        "# THE SPIDER OMEGA Report\n\n"
        "Generated: " + datetime.now(timezone.utc).isoformat()
        + "\n\n```json\n" + rendered + "\n```\n"
    )
    md_path.write_text(markdown, encoding="utf-8")
    return str(json_path), str(md_path)
