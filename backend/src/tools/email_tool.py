from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from langchain.tools import StructuredTool
from pydantic import BaseModel, EmailStr, Field

from src.config import get_settings


class EmailInput(BaseModel):
    to: EmailStr
    subject: str
    body: str


def make_email_tool() -> StructuredTool:
    async def _send(to: str, subject: str, body: str) -> str:
        s = get_settings()
        if not (s.smtp_host and s.smtp_from):
            return "error: SMTP not configured"

        def _run() -> str:
            msg = EmailMessage()
            msg["From"] = s.smtp_from
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as smtp:
                smtp.ehlo()
                try:
                    smtp.starttls()
                except Exception:
                    pass
                if s.smtp_user and s.smtp_password:
                    smtp.login(s.smtp_user, s.smtp_password)
                smtp.send_message(msg)
            return "sent"

        return await asyncio.get_running_loop().run_in_executor(None, _run)

    return StructuredTool.from_function(
        coroutine=_send,
        func=lambda **_: "async only",
        name="send_email",
        description="Send a plain-text email via configured SMTP.",
        args_schema=EmailInput,
    )
