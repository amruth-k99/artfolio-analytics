import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Determine environment and load appropriate .env file
is_debug = os.getenv("DEBUG", "True").lower()

env_file = ".env.prod" if is_debug == "false" else ".env"

print(f"Loading environment variables from: {is_debug} {env_file}")

load_dotenv(env_file)


###
#
# Why?
# - Type safety: Using Pydantic's BaseSettings provides type validation for configuration values, reducing the risk of runtime errors due to misconfigured settings.
# - Environment variable support: Automatically loads settings from .env files, which can be different for development, staging, and production environments.

# ###
class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
    deployment_email: str
    cors_origins: list[str] = ["*"]
    self_base_url: str = "http://localhost:8000"

    class Config:
        env_file = env_file


CONFIG = Settings()
