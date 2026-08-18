from jinja2 import Environment, FileSystemLoader
import os
from typing import Dict, Any, Optional
try:
    from weasyprint import HTML
    WEASY = True
except Exception:
    WEASY = False


class QuoteRenderer:
    def __init__(self, template_path: str = "templates/quote_template.html", pdf: bool = False):
        self.template_path = template_path
        self.env = Environment(loader=FileSystemLoader("./"))
        self.pdf = pdf and WEASY

    def render(self, business: Dict[str, Any], out_html_path: str, pricing: Dict[str, Any], company: Optional[Dict[str, Any]] = None) -> None:
        tpl = self.env.get_template(self.template_path)
        html = tpl.render(business=business, pricing=pricing, company=company or {})
        os.makedirs(os.path.dirname(out_html_path) or '.', exist_ok=True)
        with open(out_html_path, "w", encoding="utf-8") as f:
            f.write(html)
        if self.pdf:
            pdf_path = out_html_path.rsplit('.', 1)[0] + '.pdf'
            HTML(string=html).write_pdf(pdf_path)
