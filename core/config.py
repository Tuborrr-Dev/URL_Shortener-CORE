from pydantic_settings import SettingsConfigDict, BaseSettings


# this is written to get the files ws have in the .env file
class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
