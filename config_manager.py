from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    配置管理类，使用 pydantic_settings 从环境变量或 .env 文件加载配置。
    """
    DEVICE: str = "cuda"
    HOST: str = "0.0.0.0"
    PORT: int = 8830

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()