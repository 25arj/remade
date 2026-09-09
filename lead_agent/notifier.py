import logging

import requests

from lead_agent.qualifier import Qualification

logger = logging.getLogger(__name__)


def send_to_slack(webhook_url: str, qualification: Qualification) -> None:
    c = qualification.candidate
    text = (
        f"*New lead ({qualification.fit_score}/10)* - r/{c.subreddit}\n"
        f"*{c.title}*\n"
        f"{qualification.reasoning}\n"
        f"> Suggested opener: {qualification.suggested_opener}\n"
        f"<{c.permalink}|View post> - u/{c.author}"
    )
    response = requests.post(webhook_url, json={"text": text}, timeout=10)
    if response.status_code != 200:
        logger.error("Slack webhook failed (%s): %s", response.status_code, response.text)
