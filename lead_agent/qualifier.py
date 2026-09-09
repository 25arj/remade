import json
import logging
from dataclasses import dataclass

import anthropic

from lead_agent.reddit_source import Candidate

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"

_SCHEMA = {
    "type": "object",
    "properties": {
        "is_lead": {"type": "boolean"},
        "fit_score": {
            "type": "integer",
            "description": "0-10, how strong a fit this person is for the service",
        },
        "reasoning": {"type": "string", "description": "One or two sentences on why."},
        "suggested_opener": {
            "type": "string",
            "description": "A short, non-spammy first line to reply with, referencing their specific situation.",
        },
    },
    "required": ["is_lead", "fit_score", "reasoning", "suggested_opener"],
    "additionalProperties": False,
}


@dataclass
class Qualification:
    candidate: Candidate
    is_lead: bool
    fit_score: int
    reasoning: str
    suggested_opener: str


def qualify(client: anthropic.Anthropic, service_description: str, candidate: Candidate) -> Qualification:
    system = (
        "You score Reddit posts as sales leads for the following service:\n\n"
        f"{service_description}\n\n"
        "Score how strong a fit the poster is: are they clearly describing a manual, "
        "repetitive, time-consuming process that this service would solve, and do they "
        "seem to be a real potential buyer (not a vendor pitching their own tool, not "
        "someone just venting with no buying intent, not a student/hobby project)? "
        "Be skeptical - most posts are not real leads."
    )
    user_content = (
        f"Subreddit: r/{candidate.subreddit}\n"
        f"Title: {candidate.title}\n"
        f"Body: {candidate.body or '(no body text)'}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user_content}],
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": _SCHEMA},
        },
    )

    text = next(block.text for block in response.content if block.type == "text")
    data = json.loads(text)

    return Qualification(
        candidate=candidate,
        is_lead=data["is_lead"],
        fit_score=data["fit_score"],
        reasoning=data["reasoning"],
        suggested_opener=data["suggested_opener"],
    )
