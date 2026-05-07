from pathlib import Path
import json
from datetime import datetime

RUNS = Path("runs")
REPORTS = Path("reports")

def save_run(payload: dict):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    RUNS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    (RUNS / f"{ts}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (REPORTS / f"{ts}.md").write_text(payload.get("report", ""), encoding="utf-8")
    return ts

def build_report(data: dict) -> str:
    lines = [f"# Daily Research Brief: {data.get('topic', 'Unknown')}", ""]
    lines.append("## Top sources")
    for s in data.get("sources", [])[:10]:
        lines.append(f"- {s['url']} | authority {s['authority_score']} | relevance {s['relevance_score']}")
    lines.append("")
    lines.append("## Synthesis")
    lines.append(data.get("synthesis", ""))
    return "\n".join(lines)
