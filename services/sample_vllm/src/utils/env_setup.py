import os
import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentSettings(BaseSettings):
    # Fixed - model_name_map - pre-downloaded
    MODEL_IDX: dict
    ATTACK_PROMPT_MAX_TOKEN_LENGTH: int = 256
    VLLM_RESPONSE_MAX_TOKEN_LENGTH: int = 256
    MODEL_FILES_LOCATION: str = "./models"


env_settings = EnvironmentSettings()
