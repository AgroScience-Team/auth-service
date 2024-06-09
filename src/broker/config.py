from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    BOOTSTRAP_SERVERS: str

    model_config = SettingsConfigDict(
        env_prefix="KAFKA_",
        env_file=".env"
    )


kafka_settings = KafkaSettings()
