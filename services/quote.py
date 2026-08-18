from jinja2 import Environment, FileSystemLoader
import os
try:
    from weasyprint import HTML
    WEASY = True
except Exception:
    WEASY = False

class QuoteRenderer:
    def __init__(self, template_path="templates/quote_template.html", pdf=False):
        self.template_path = template_path
        self.env = Environment(loader=FileSystemLoader("./"))
        self.pdf = pdf and WEASY

    def render(self, business, out_html_path, pricing):
        tpl = self.env.get_template(self.template_path)
        html = tpl.render(business=business, pricing=pricing)
        with open(out_html_path, "w", encoding="utf-8") as f:
            f.write(html)
        if self.pdf:
            pdf_path = out_html_path.rsplit(".",1)[0] + ".pdf"
            HTML(string=html).write_pdf(pdf_path)
