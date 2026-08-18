import smtplib
from email.message import EmailMessage
import os
from typing import Optional, Dict
import logging

logger = logging.getLogger("localia.mailer")


class Mailer:
    def __init__(self, smtp_cfg: Optional[Dict[str, Any]] = None):
        self.cfg = smtp_cfg or {}

    def send_quote(self, to_email: str, subject: str, html_body: str, attachment_path: Optional[str] = None) -> None:
        host = self.cfg.get("host")
        port = int(self.cfg.get("port", 587))
        user = self.cfg.get("username")
        password = self.cfg.get("password")
        use_tls = bool(self.cfg.get("use_tls", True))
        from_email = self.cfg.get("from_email") or user

        if not host or not user or not password:
            raise ValueError("SMTP configuration incomplete. Please set host, username and password.")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content("Este e-mail contém um orçamento em HTML. Verifique a versão em HTML ou anexo PDF.")
        msg.add_alternative(html_body, subtype="html")

        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as f:
                    data = f.read()
                msg.add_attachment(data, maintype="application", subtype="pdf", filename=os.path.basename(attachment_path))
            except Exception:
                logger.exception("Falha ao anexar arquivo %s", attachment_path)

        if use_tls:
            server = smtplib.SMTP(host, port, timeout=20)
            try:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)
            finally:
                server.quit()
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=20)
            try:
                server.login(user, password)
                server.send_message(msg)
            finally:
                server.quit()

        logger.info("E-mail enviado para %s (subject=%s)", to_email, subject)
