# Async email sender
from email.message import EmailMessage
from aiosmtplib import send


from src.settings.mail import mail_settings


async def send_otp_email(to_email: str, otp: str):
    message = EmailMessage()
    message["From"] = mail_settings.EMAIL_SENDER  # your email
    message["To"] = to_email
    message["Subject"] = "Your Email Verification OTP"
    message.set_content(f"Your OTP is: {otp}\nIt is valid for 10 minutes.")

    await send(
        message,
        hostname=mail_settings.SMTP_HOST,
        port=int(mail_settings.SMTP_PORT),
        username=mail_settings.SMTP_USER,
        password=mail_settings.SMTP_PASS,
        start_tls=True,
    )
