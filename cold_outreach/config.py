import os
from dataclasses import dataclass

import yaml
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ColdOutreachConfig:
    icp_description: str
    search_queries: list
    results_per_query: int
    daily_send_cap: int
    subject_line: str
    message_template_file: str
    sheet_tab_name: str
    state_file: str

    google_search_api_key: str
    google_search_cx: str
    google_service_account_file: str
    google_sheet_id: str
    gmail_oauth_credentials_file: str
    gmail_token_file: str
    from_email: str
    slack_webhook_url: str


def load_config(path: str = "cold_outreach_config.yaml") -> ColdOutreachConfig:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    required_env = {
        "GOOGLE_SEARCH_API_KEY": "google_search_api_key",
        "GOOGLE_SEARCH_CX": "google_search_cx",
        "GOOGLE_SERVICE_ACCOUNT_FILE": "google_service_account_file",
        "GOOGLE_SHEET_ID": "google_sheet_id",
        "GMAIL_OAUTH_CREDENTIALS_FILE": "gmail_oauth_credentials_file",
        "FROM_EMAIL": "from_email",
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

    return ColdOutreachConfig(
        icp_description=raw["icp_description"].strip(),
        search_queries=raw["search_queries"],
        results_per_query=raw.get("results_per_query", 10),
        daily_send_cap=raw.get("daily_send_cap", 25),
        subject_line=raw.get("subject_line", "quick question"),
        message_template_file=raw.get("message_template_file", "cold_outreach/message_template.txt"),
        sheet_tab_name=raw.get("sheet_tab_name", "Cold Email Leads"),
        state_file=raw.get("state_file", "state/cold_outreach_state.json"),
        gmail_token_file=os.environ.get("GMAIL_TOKEN_FILE", "state/gmail_token.json"),
        slack_webhook_url=os.environ.get("SLACK_WEBHOOK_URL", ""),
        **env_values,
    )
