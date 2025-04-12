from functools import cache
from pydantic import Field
from pydantic_settings import BaseSettings


class RDBSettings(BaseSettings):
    DB_HOST: str = Field(min_length=1)
    DB_PORT: str = Field(min_length=1)
    DB_NAME: str = Field(min_length=1)
    DB_USER: str = Field(min_length=1)
    DB_PASSWORD: str = Field(min_length=1)

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@cache
def get_rdb_settings():
    return RDBSettings.model_validate({})


rdb_settings = get_rdb_settings()
