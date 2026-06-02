# -*- coding: utf-8 -*-
"""
bot_auth.py — Authentication and rate-limiting helpers for the Bot Gateway.

Two responsibilities:
  1. validate_bot_api_key   — check the X-Bot-Secret header against the
                              'bot_gateway.webhook_secret' system parameter.
  2. check_rate_limit       — sliding-window counter per IP address.

Production note:
  The rate limiter uses an in-memory defaultdict, which is suitable for
  single-process Odoo deployments.  For multi-worker environments, replace
  _rate_store with a Redis backend:

      import redis
      _redis = redis.Redis()

      def check_rate_limit(ip):
          key = f"rl:bot:{ip}"
          count = _redis.incr(key)
          if count == 1:
              _redis.expire(key, RATE_WINDOW)
          return count <= RATE_LIMIT
"""

import time
import logging
from collections import defaultdict

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter configuration
# ---------------------------------------------------------------------------
RATE_LIMIT  = 30   # maximum requests allowed
RATE_WINDOW = 60   # per sliding window (seconds)

# In-memory store: { ip_address: [epoch_timestamp, ...] }
_rate_store: dict = defaultdict(list)


def validate_bot_api_key(env, provided_key: str) -> bool:
    """
    Return True if *provided_key* matches the configured webhook secret.

    The secret is stored in ir.config_parameter under key
    'bot_gateway.webhook_secret'.  An empty or missing secret always
    rejects all requests (fail-closed).
    """
    if not provided_key:
        _logger.debug("BotAuth: no API key provided")
        return False

    expected = env['ir.config_parameter'].sudo().get_param(
        'bot_gateway.webhook_secret', ''
    )
    if not expected:
        _logger.warning(
            "BotAuth: 'bot_gateway.webhook_secret' is not set — "
            "all bot webhook requests will be rejected."
        )
        return False

    valid = provided_key == expected
    if not valid:
        _logger.warning("BotAuth: invalid webhook secret from client")
    return valid


def check_rate_limit(ip: str) -> bool:
    """
    Sliding-window rate limiter.

    Returns True  → request is within limit (proceed).
    Returns False → limit exceeded (respond 429).
    """
    now = time.monotonic()
    window_start = now - RATE_WINDOW

    # Evict timestamps older than the window
    _rate_store[ip] = [t for t in _rate_store[ip] if t > window_start]

    if len(_rate_store[ip]) >= RATE_LIMIT:
        _logger.warning(
            "BotGateway: rate limit exceeded for IP %s (%d/%d req/%ds)",
            ip, len(_rate_store[ip]), RATE_LIMIT, RATE_WINDOW,
        )
        return False

    _rate_store[ip].append(now)
    return True
