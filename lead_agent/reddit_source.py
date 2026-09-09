import logging
from dataclasses import dataclass

import praw

from lead_agent.config import Config

logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    id: str
    title: str
    body: str
    subreddit: str
    author: str
    permalink: str
    created_utc: float


def make_reddit_client(config: Config) -> praw.Reddit:
    return praw.Reddit(
        client_id=config.reddit_client_id,
        client_secret=config.reddit_client_secret,
        user_agent=config.reddit_user_agent,
    )


def find_candidates(reddit: praw.Reddit, config: Config, seen_ids: set) -> list:
    """Search the configured subreddits for the configured keywords via
    Reddit's own search API. No scraping, no login automation - this stays
    fully within Reddit's API terms.
    """
    multireddit = reddit.subreddit("+".join(config.subreddits))
    candidates_by_id = {}

    for keyword in config.keywords:
        try:
            results = multireddit.search(
                keyword,
                sort="new",
                time_filter=config.time_filter,
                limit=config.results_per_keyword,
            )
            for submission in results:
                if submission.id in seen_ids or submission.id in candidates_by_id:
                    continue
                candidates_by_id[submission.id] = Candidate(
                    id=submission.id,
                    title=submission.title or "",
                    body=(submission.selftext or "")[:2000],
                    subreddit=str(submission.subreddit),
                    author=str(submission.author) if submission.author else "[deleted]",
                    permalink=f"https://reddit.com{submission.permalink}",
                    created_utc=submission.created_utc,
                )
        except Exception:
            logger.exception("Reddit search failed for keyword %r", keyword)

    return list(candidates_by_id.values())
