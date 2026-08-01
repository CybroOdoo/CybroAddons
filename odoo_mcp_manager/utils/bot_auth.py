# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
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

import hmac
import time
import logging
from collections import defaultdict

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter configuration
# ---------------------------------------------------------------------------
RATE_LIMIT  = 30   # maximum requests allowed
RATE_WINDOW = 60   # per sliding window (seconds)

# Drop IP buckets that have been idle for this long, so the in-memory store
# cannot grow unbounded under a spray of distinct source addresses.
_RATE_STORE_MAX_IDLE = RATE_WINDOW * 10

# In-memory store: { ip_address: [epoch_timestamp, ...] }
# NOTE: per-process only. For multi-worker deployments replace with a shared
# backend (e.g. Redis) — see the module docstring for a drop-in example.
_rate_store: dict = defaultdict(list)


def secure_compare(provided: str, expected: str) -> bool:
    """
    Constant-time comparison of two secrets.

    Wraps :func:`hmac.compare_digest` and guards against ``None``/empty inputs
    so callers never leak length or content through timing or exceptions.
    """
    if not provided or not expected:
        return False
    return hmac.compare_digest(str(provided), str(expected))


def validate_bot_api_key(env, provided_key: str) -> bool:
    """
    Return True if *provided_key* matches the configured webhook secret.

    The secret is stored in ir.config_parameter under key
    'bot_gateway.webhook_secret'.  An empty or missing secret always
    rejects all requests (fail-closed). The comparison is constant-time.
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

    valid = secure_compare(provided_key, expected)
    if not valid:
        _logger.warning("BotAuth: invalid webhook secret from client")
    return valid


def _evict_idle_ips(now: float) -> None:
    """Remove IP buckets whose most recent hit is older than the idle cutoff."""
    cutoff = now - _RATE_STORE_MAX_IDLE
    stale = [ip for ip, hits in _rate_store.items() if not hits or hits[-1] <= cutoff]
    for ip in stale:
        del _rate_store[ip]


def check_rate_limit(ip: str) -> bool:
    """
    Sliding-window rate limiter.

    Returns True  → request is within limit (proceed).
    Returns False → limit exceeded (respond 429).
    """
    now = time.monotonic()
    window_start = now - RATE_WINDOW

    # Opportunistically evict long-idle IP buckets to bound memory use.
    if len(_rate_store) > 1024:
        _evict_idle_ips(now)

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
