import os
from dataclasses import dataclass

import yaml
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    service_description: str
    subreddits: list
    keywords: list
    results_per_keyword: int
    time_filter: str
    score_threshold: int
    max_new_posts_per_run: int
    state_file: str

    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str
    anthropic_api_key: str
    slack_webhook_url: str
    google_service_account_file: str
    google_sheet_id: str


def load_config(path: str = "config.yaml") -> Config:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    required_env = {
        "REDDIT_CLIENT_ID": "reddit_client_id",
        "REDDIT_CLIENT_SECRET": "reddit_client_secret",
        "REDDIT_USER_AGENT": "reddit_user_agent",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "SLACK_WEBHOOK_URL": "slack_webhook_url",
        "GOOGLE_SERVICE_ACCOUNT_FILE": "google_service_account_file",
        "GOOGLE_SHEET_ID": "google_sheet_id",
    }
    env_values = {}
    missing = []
    for env_key, field_name in required_env.items():
        value = os.environ.get(env_key)
        if not value:
            missing.append(env_key)
        env_values[field_name] = value
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )

    return Config(
        service_description=raw["service_description"].strip(),
        subreddits=raw["subreddits"],
        keywords=raw["keywords"],
        results_per_keyword=raw.get("results_per_keyword", 15),
        time_filter=raw.get("time_filter", "week"),
        score_threshold=raw.get("score_threshold", 7),
        max_new_posts_per_run=raw.get("max_new_posts_per_run", 40),
        state_file=raw.get("state_file", "state/seen_posts.json"),
        **env_values,
    )
