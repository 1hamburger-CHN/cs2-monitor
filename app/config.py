"""Application configuration from environment variables and YAML file."""
import os
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+aiomysql://cs2monitor:password@localhost:3306/cs2monitor"
    encryption_key: str = ""
    secret_key: str = "dev-secret-change-in-production"
    admin_password_hash: str = ""
    crawler_interval_seconds: int = 300
    crawler_timeout: int = 15
    crawler_max_concurrent: int = 5
    crawler_user_agent: str = "CS2-Monitor/1.0"
    inventory_interval_hours: int = 6
    inventory_min_value: float = 10.0
    retention_raw_days: int = 30
    retention_cleanup_hour: int = 2
    daily_report_hour: int = 20
    notification_retry_count: int = 1
    notification_retry_delay: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @classmethod
    def from_yaml(cls, yaml_path: str = "config.yaml") -> "Settings":
        settings = cls()
        if Path(yaml_path).exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)
            if yaml_config:
                if "crawler" in yaml_config:
                    for k, v in yaml_config["crawler"].items():
                        key = f"crawler_{k}"
                        if hasattr(settings, key):
                            setattr(settings, key, v)
                if "inventory" in yaml_config:
                    inv = yaml_config["inventory"]
                    if "min_value_threshold" in inv:
                        settings.inventory_min_value = inv["min_value_threshold"]
                    if "interval_hours" in inv:
                        settings.inventory_interval_hours = inv["interval_hours"]
                if "retention" in yaml_config:
                    r = yaml_config["retention"]
                    if "raw_days" in r:
                        settings.retention_raw_days = r["raw_days"]
                    if "cleanup_hour" in r:
                        settings.retention_cleanup_hour = r["cleanup_hour"]
                if "daily_report" in yaml_config:
                    settings.daily_report_hour = yaml_config["daily_report"].get("hour", 20)
                if "notification" in yaml_config:
                    n = yaml_config["notification"]
                    if "retry_count" in n:
                        settings.notification_retry_count = n["retry_count"]
                    if "retry_delay" in n:
                        settings.notification_retry_delay = n["retry_delay"]
        return settings


settings = Settings.from_yaml()
