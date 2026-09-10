# Lead Agent

Two lanes, one shared Google Sheet as the lead log:

- **`lead_agent/`** - finds Reddit posts from people who are good leads for
  an automation-selling service, scores them with Claude, logs them to the
  Sheet, and posts the good ones to Slack. You reply by hand - these are
  warm, high-intent, low-volume.
- **`cold_outreach/`** - finds company contact emails at volume, sends each
  one your message once via Gmail, logs everything to the same Sheet, and
  watches for replies. The moment a lead replies, it's marked and never
  emailed again automatically - that's your cue to take over manually.

Neither lane touches LinkedIn or Instagram. Scraping either one, or
automating a logged-in session, breaks their terms of service and risks
account bans or legal exposure. If you want those sources later, the clean
way in is a search-engine API querying `site:linkedin.com` for public
posts, not direct scraping - ask and I'll wire that in as another source
module.

## Reddit lane - how it works

1. `reddit_source.py` searches your configured subreddits for your
   configured keywords via PRAW (Reddit's official API).
2. `qualifier.py` sends each new post to Claude, which scores 0-10 how good
   a fit the poster is for your service and writes a suggested opening
   line.
3. `sheet_log.py` logs every qualified lead to the "Reddit Leads" tab.
4. `notifier.py` posts the same leads to Slack.
5. `state.py` tracks which post IDs have already been processed
   (`state/seen_posts.json`) so nothing gets scored or notified twice.

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a Reddit "script" app at https://www.reddit.com/prefs/apps to get
   a client ID and secret.
3. Create a Slack incoming webhook: https://api.slack.com/messaging/webhooks
4. Get an Anthropic API key: https://console.anthropic.com/
5. Set up the Google Sheet (see [Google Sheet setup](#google-sheet-setup)
   below - shared with the cold email lane).
6. Copy `.env.example` to `.env` and fill in the values.
7. Edit `config.yaml`:
   - `service_description` - describe what you're selling, in your own
     words. This is the context Claude uses to score fit.
   - `subreddits` / `keywords` - tune to your niche.
   - `score_threshold` - raise it if Slack gets too much noise, lower it if
     you want more (less qualified) leads.

### Run

```bash
python -m lead_agent.main
```

## Cold email lane - how it works

1. `source.py` runs your configured queries against Google's Custom Search
   API to find company websites matching your ICP, then does a plain GET of
   each site's homepage (and `/contact` as a fallback) to pick up a publicly
   listed email address. No login, no scraping behind auth - just reading
   pages that are already public.
2. `sender.py` sends each new lead your message once (from
   `message_template.txt`), logs it to the "Cold Email Leads" tab, and
   stops once it hits `daily_send_cap` for the day.
3. `reply_watcher.py` runs before every send batch, checks Gmail for a
   reply from each contacted address, and marks it `REPLIED - reply
   manually` in the Sheet + Slack the moment one comes in. That address is
   never emailed again by this pipeline.
4. `state.py` (`state/cold_outreach_state.json`) is what makes the "only
   ever message once, stop forever on reply" rule work.

### Setup

1. Google Cloud Console (one project covers Sheets, Search, and Gmail):
   - Enable the **Google Sheets API**, **Custom Search API**, and **Gmail
     API**.
   - Create a **service account**, download its JSON key, save it as
     `service_account.json`. Share your target Google Sheet with the
     service account's email address (Editor access).
   - Create an **OAuth client ID** (type: Desktop app), download its JSON
     as `gmail_credentials.json`. First run opens a browser to authorize
     your own Gmail inbox; after that the token is cached and refreshed
     automatically.
2. Programmable Search Engine: create one at
   https://programmablesearchengine.google.com/ (set it to search the
   whole web), grab its `cx` ID, and get an API key for the Custom Search
   API at https://console.cloud.google.com/apis/credentials.
3. Copy `.env.example` to `.env` and fill in the Google Sheets / Search /
   Gmail values plus `FROM_EMAIL`.
4. Edit `cold_outreach_config.yaml`:
   - `search_queries` - tune to your ICP.
   - `daily_send_cap` - **start at 20-30, not 100.** A fresh Gmail account
     sending identical cold emails to strangers at high volume gets flagged
     as spam or suspended - there's no free way around mailbox warmup. Raise
     this gradually over a few weeks. If you outgrow it, move sending to a
     dedicated cold email tool (Instantly, Smartlead) - `source.py` and the
     Sheet logging stay the same, only `sender.py`'s send step changes.
5. Edit `cold_outreach/message_template.txt` with the actual message you
   want sent to every lead. Use `{company}` to personalize.

### Run

```bash
python -m cold_outreach.main
```

## Google Sheet setup

Both lanes write to one spreadsheet (different tabs: "Reddit Leads" and
"Cold Email Leads"), so you have one place to see everything.

1. Create a new Google Sheet, copy its ID out of the URL
   (`docs.google.com/spreadsheets/d/<THIS PART>/edit`).
2. Share it with your service account's email (from the Google Cloud setup
   above), Editor access.
3. Put the ID in `GOOGLE_SHEET_ID` in `.env`.

Tabs and headers are created automatically on first run.

## Running both on a schedule

```
0 * * * *  cd /path/to/remade && /path/to/venv/bin/python -m lead_agent.main    >> lead_agent.log 2>&1
0 * * * *  cd /path/to/remade && /path/to/venv/bin/python -m cold_outreach.main >> cold_outreach.log 2>&1
```

## Cost

Each new Reddit post costs one small Claude call (`claude-opus-5`, low
effort, ~500 output tokens). `max_new_posts_per_run` in `config.yaml` caps
spend per run. The cold email lane has no Claude calls - Custom Search
(100 free queries/day) and Gmail sending are both free at this volume.
