from functools import cache
from pydantic import Field
from pydantic_settings import BaseSettings


class MailSettings(BaseSettings):
    EMAIL_SENDER: str = Field(min_length=1)
    SMTP_HOST: str = Field(min_length=1)
    SMTP_PORT: str = Field(min_length=1)
    SMTP_USER: str = Field(min_length=1)
    SMTP_PASS: str = Field(min_length=1)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@cache
def get_mail_settings():
    return MailSettings.model_validate({})


mail_settings = get_mail_settings()
