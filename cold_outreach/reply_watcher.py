import logging
from datetime import datetime, timezone

import requests

from cold_outreach import gmail_client
from cold_outreach import state as state_mod
from common.sheets import append_row, get_sheet

logger = logging.getLogger(__name__)


def _notify_slack(webhook_url: str, text: str) -> None:
    response = requests.post(webhook_url, json={"text": text}, timeout=10)
    if response.status_code != 200:
        logger.error("Slack webhook failed (%s): %s", response.status_code, response.text)


def run(config) -> None:
    """Checks every lead we've emailed but haven't heard back from yet.
    The moment a reply shows up, that lead is marked REPLIED and is never
    contacted again by this pipeline - from there it's yours to answer by
    hand.
    """
    st = state_mod.load_state(config.state_file)
    pending = [email for email, record in st.items() if record["status"] == "sent"]
    if not pending:
        return

    gmail = gmail_client.get_gmail_service(config.gmail_oauth_credentials_file, config.gmail_token_file)
    worksheet = get_sheet(config.google_service_account_file, config.google_sheet_id, config.sheet_tab_name)

    replied = 0
    for email in pending:
        record = st[email]
        if not gmail_client.has_reply_from(gmail, email, record["sent_at"]):
            continue

        state_mod.mark_replied(st, email)
        append_row(
            worksheet,
            [
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                record["company"],
                record["website"],
                email,
                "REPLIED - reply manually",
                record["sent_at"],
                record["replied_at"],
            ],
        )
        if config.slack_webhook_url:
            try:
                _notify_slack(
                    config.slack_webhook_url,
                    f"*{record['company']}* ({email}) replied to your cold email - go take over, check your inbox.",
                )
            except Exception:
                logger.exception("Failed to notify Slack of reply from %s", email)
        replied += 1

    state_mod.save_state(config.state_file, st)
    logger.info("%d new repl(y/ies) detected", replied)
