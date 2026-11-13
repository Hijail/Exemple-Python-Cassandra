import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    cassandra_hosts: List[str]
    cassandra_port: int
    keyspace: str
    local_dc: str
    input_path: Path
    baseline_path: Path
    log_level: str


def get_settings() -> Settings:
    hosts = os.getenv("CASSANDRA_HOSTS", "127.0.0.1")
    return Settings(
        cassandra_hosts=[host.strip() for host in hosts.split(",") if host.strip()],
        cassandra_port=int(os.getenv("CASSANDRA_PORT", "9042")),
        keyspace=os.getenv("CASSANDRA_KEYSPACE", "game_analytics"),
        local_dc=os.getenv("CASSANDRA_LOCAL_DC", "datacenter1"),
        input_path=Path(os.getenv("INPUT_PATH", "data/events.json")),
        baseline_path=Path(os.getenv("PURCHASE_BASELINE_PATH", "data/purchase_baseline.json")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
