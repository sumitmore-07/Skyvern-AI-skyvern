from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from schemas import ComparisonRow

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def render_report(rows: list[ComparisonRow], shops: list[str], output_dir: Path) -> Path:
    """Render the comparison to a self-contained HTML file and return its path."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]))
    now = datetime.now()
    html = env.get_template("report.html").render(rows=rows, shops=shops, generated=now.strftime("%Y-%m-%d %H:%M"))
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"price_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    path.write_text(html, encoding="utf-8")
    return path
