from datetime import datetime, timezone

from common.sheets import append_row, ensure_header, get_sheet
from lead_agent.qualifier import Qualification

HEADER = ["Date", "Score", "Subreddit", "Title", "Author", "Permalink", "Reasoning", "Suggested Opener"]


def get_worksheet(service_account_file: str, sheet_id: str):
    worksheet = get_sheet(service_account_file, sheet_id, "Reddit Leads")
    ensure_header(worksheet, HEADER)
    return worksheet


def log_lead(worksheet, qualification: Qualification) -> None:
    c = qualification.candidate
    append_row(
        worksheet,
        [
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            qualification.fit_score,
            c.subreddit,
            c.title,
            c.author,
            c.permalink,
            qualification.reasoning,
            qualification.suggested_opener,
        ],
    )
