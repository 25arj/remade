import logging
from datetime import datetime, timezone

from cold_outreach import gmail_client
from cold_outreach import state as state_mod
from cold_outreach.source import find_candidate_companies
from common.sheets import append_row, ensure_header, get_sheet

logger = logging.getLogger(__name__)

HEADER = ["Date Found", "Company", "Website", "Email", "Status", "Sent At", "Replied At"]


def run(config) -> None:
    st = state_mod.load_state(config.state_file)
    worksheet = get_sheet(config.google_service_account_file, config.google_sheet_id, config.sheet_tab_name)
    ensure_header(worksheet, HEADER)

    with open(config.message_template_file, "r") as f:
        template = f.read()

    seen_emails = set(st.keys())
    candidates = find_candidate_companies(config, seen_emails)
    logger.info("Found %d new candidate compan(y/ies)", len(candidates))

    remaining = max(0, config.daily_send_cap - state_mod.count_sent_today(st))
    logger.info("%d send(s) remaining in today's cap of %d", remaining, config.daily_send_cap)

    gmail = gmail_client.get_gmail_service(config.gmail_oauth_credentials_file, config.gmail_token_file)

    sent = 0
    for lead in candidates:
        if sent >= remaining:
            break

        body = template.replace("{company}", lead.company)
        try:
            gmail_client.send_email(gmail, config.from_email, lead.email, config.subject_line, body)
        except Exception:
            logger.exception("Failed to send to %s", lead.email)
            continue

        state_mod.mark_sent(st, lead.email, lead.company, lead.website)
        append_row(
            worksheet,
            [
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                lead.company,
                lead.website,
                lead.email,
                "sent",
                st[lead.email]["sent_at"],
                "",
            ],
        )
        sent += 1

    state_mod.save_state(config.state_file, st)
    logger.info("Sent %d new cold email(s)", sent)
