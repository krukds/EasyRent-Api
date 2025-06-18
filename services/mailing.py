import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import config


def send_email(to_email, subject, body):
    smtp_port = config.EMAIL_SMTP_PORT
    smtp_server = config.EMAIL_SMTP_SERVER
    from_email = config.EMAIL_LOGIN
    app_password = config.EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, app_password)
        server.send_message(msg)

    print("✅ Email надіслано")


async def send_email_async(to_email, subject, body):
    await asyncio.to_thread(send_email, to_email, subject, body)
