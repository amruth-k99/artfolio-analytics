import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Determine environment and load appropriate .env file
is_debug = os.getenv("DEBUG", "True").lower()

env_file = ".env.prod" if is_debug == "false" else ".env"

print(f"Loading environment variables from: {is_debug} {env_file}")

load_dotenv(env_file)


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

    class Config:
        env_file = env_file


CONFIG = Settings()
