"""Environment configuration. No default API credential is shipped."""
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urlsplit


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='TASK_', env_file='.env', extra='ignore', hide_input_in_errors=True)
    api_key: SecretStr
    database_url: str = 'sqlite:///./tasks.db'
    cors_origins: list[str] = []
    docs_enabled: bool = True

    @field_validator('api_key')
    @classmethod
    def strong_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if len(raw) < 32 or raw.strip() != raw or raw.lower().startswith(('replace', 'change', 'your-')):
            raise ValueError('Set TASK_API_KEY to a randomly generated key of at least 32 characters')
        return value

    @field_validator('cors_origins')
    @classmethod
    def exact_origins(cls, values: list[str]) -> list[str]:
        for origin in values:
            parts = urlsplit(origin)
            if (parts.scheme not in {'http', 'https'} or not parts.netloc or '*' in origin
                    or parts.path or parts.query or parts.fragment or parts.username):
                raise ValueError('CORS origins must be exact http(s) origins without paths or wildcards')
        return values
