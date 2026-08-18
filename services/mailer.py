import smtplib
import os
from email.message import EmailMessage
import logging

logger = logging.getLogger("localia.mailer")

class Mailer:
    def __init__(self, smtp_cfg=None):
        # smtp_cfg: dict with host, port, username, password, use_tls, from_email
        self.cfg = smtp_cfg or {}

    def send_quote(self, to_email, subject, html_body, attachment_path=None):
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

        if attachment_path:
            try:
                with open(attachment_path, "rb") as f:
                    data = f.read()
                maintype = "application"
                subtype = "pdf"
                filename = os.path.basename(attachment_path)
                msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
            except Exception as e:
                logger.exception("Não foi possível anexar arquivo %s: %s", attachment_path, e)

        # send
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
