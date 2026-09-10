import logging

import anthropic

from lead_agent.config import load_config
from lead_agent.notifier import send_to_slack
from lead_agent.qualifier import qualify
from lead_agent.reddit_source import find_candidates, make_reddit_client
from lead_agent.sheet_log import get_worksheet, log_lead
from lead_agent.state import load_seen_ids, save_seen_ids

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run() -> None:
    config = load_config()
    seen_ids = load_seen_ids(config.state_file)

    reddit = make_reddit_client(config)
    candidates = find_candidates(reddit, config, seen_ids)
    logger.info("Found %d new candidate post(s)", len(candidates))

    candidates = candidates[: config.max_new_posts_per_run]
    if not candidates:
        return

    claude = anthropic.Anthropic(api_key=config.anthropic_api_key)
    worksheet = get_worksheet(config.google_service_account_file, config.google_sheet_id)
    leads_sent = 0

    for candidate in candidates:
        seen_ids.add(candidate.id)
        try:
            result = qualify(claude, config.service_description, candidate)
        except Exception:
            logger.exception("Failed to qualify post %s", candidate.id)
            continue

        logger.info(
            "r/%s '%s' -> score=%d is_lead=%s",
            candidate.subreddit,
            candidate.title[:60],
            result.fit_score,
            result.is_lead,
        )

        if result.is_lead and result.fit_score >= config.score_threshold:
            try:
                log_lead(worksheet, result)
            except Exception:
                logger.exception("Failed to log lead to Google Sheet for post %s", candidate.id)
            try:
                send_to_slack(config.slack_webhook_url, result)
                leads_sent += 1
            except Exception:
                logger.exception("Failed to send Slack notification for post %s", candidate.id)

    save_seen_ids(config.state_file, seen_ids)
    logger.info("Run complete: %d lead(s) sent to Slack", leads_sent)


if __name__ == "__main__":
    run()
