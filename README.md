# Lead Agent

Finds Reddit posts from people who are good leads for an automation-selling
service, scores them with Claude, and posts the good ones to Slack.

Scoped to Reddit only, using Reddit's official search API. LinkedIn and
Instagram are deliberately left out - scraping either one (or automating a
logged-in session) breaks their terms of service and risks account bans or
legal exposure. If you want those sources later, the clean way in is a
search-engine API (Serper.dev, SerpAPI, Bing) querying `site:linkedin.com`
/ `site:instagram.com` for public posts, not direct scraping - ask and I'll
wire that in as another source module.

## How it works

1. `reddit_source.py` searches your configured subreddits for your
   configured keywords via PRAW (Reddit's official API).
2. `qualifier.py` sends each new post to Claude, which scores 0-10 how good
   a fit the poster is for your service and writes a suggested opening
   line.
3. `notifier.py` posts everything scoring at or above your threshold to
   Slack.
4. `state.py` tracks which post IDs have already been processed
   (`state/seen_posts.json`) so nothing gets scored or notified twice
   across runs.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a Reddit "script" app at https://www.reddit.com/prefs/apps to get
   a client ID and secret.
3. Create a Slack incoming webhook: https://api.slack.com/messaging/webhooks
4. Get an Anthropic API key: https://console.anthropic.com/
5. Copy `.env.example` to `.env` and fill in all four values.
6. Edit `config.yaml`:
   - `service_description` - describe what you're selling, in your own
     words. This is the context Claude uses to score fit.
   - `subreddits` / `keywords` - tune to your niche.
   - `score_threshold` - raise it if Slack gets too much noise, lower it if
     you want more (less qualified) leads.

## Run

```bash
python -m lead_agent.main
```

Run it on a schedule (e.g. every hour) with cron:

```
0 * * * * cd /path/to/remade && /path/to/venv/bin/python -m lead_agent.main >> lead_agent.log 2>&1
```

## Cost

Each new post costs one small Claude call (`claude-opus-5`, low effort,
~500 output tokens). `max_new_posts_per_run` in `config.yaml` caps spend
per run regardless of how many matches Reddit returns.
