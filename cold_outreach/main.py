import logging

from cold_outreach import reply_watcher, sender
from cold_outreach.config import load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run() -> None:
    config = load_config()
    # Check for replies before sending anything new, so a lead that just
    # replied never gets a second automated email in the same run.
    reply_watcher.run(config)
    sender.run(config)


if __name__ == "__main__":
    run()
