import os
"""Web Push notification sender using VAPID."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# VAPID keys (generate once: npx web-push generate-vapid-keys)
VAPID_CLAIMS = {
    "sub": "mailto:admin@cs2monitor.local"
}
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")

SUBS_FILE = Path("data/push_subscriptions.json")


def _load_subs() -> dict:
    if SUBS_FILE.exists():
        return json.loads(SUBS_FILE.read_text())
    return {}


async def send_web_push(title: str, body: str, tag: str = "cs2-alert") -> int:
    """Send Web Push to all subscribed users. Returns count sent."""
    subs = _load_subs()
    if not subs:
        return 0

    if not VAPID_PRIVATE_KEY:
        logger.warning("VAPID keys not configured, skipping Web Push")
        return 0

    try:
        from pywebpush import WebPusher, WebPushException
    except ImportError:
        logger.warning("pywebpush not installed, skipping Web Push")
        return 0

    sent = 0
    for user_id, sub in subs.items():
        try:
            WebPusher(sub).send(
                json.dumps({"title": title, "body": body, "tag": tag}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
            sent += 1
        except WebPushException as e:
            logger.warning(f"Web Push failed for user {user_id}: {e}")
            # Remove expired subscriptions
            if e.response and e.response.status_code in (404, 410):
                _remove_sub(user_id)
        except Exception as e:
            logger.error(f"Web Push error for user {user_id}: {e}")

    logger.info(f"Web Push sent to {sent}/{len(subs)} users")
    return sent


def _remove_sub(user_id: str):
    subs = _load_subs()
    if user_id in subs:
        del subs[user_id]
        SUBS_FILE.write_text(json.dumps(subs, indent=2))
