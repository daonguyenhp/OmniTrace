import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    service_name: str = field(
        default_factory=lambda: os.getenv("SERVICE_NAME", "omnitrace")
    )
    record_prompt: bool = field(
        default_factory=lambda: os.getenv("RECORD_PROMPT", "true").lower() in ("true", "1", "yes", "t")
    )
    oracle_budget: int = field(
        default_factory=lambda: int(os.getenv("ORACLE_BUDGET", "50"))
    )

def get_settings() -> Settings:
    return Settings()