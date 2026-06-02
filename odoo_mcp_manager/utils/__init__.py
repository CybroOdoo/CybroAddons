# -*- coding: utf-8 -*-
"""
Utils package for odoo_mcp_manager.

This package supersedes the top-level utils.py file and adds the
bot_auth helpers.  The mcp_endpoint controller imports utils.dumps()
which continues to work via this __init__.py.
"""

import json
import datetime
import logging

_logger = logging.getLogger(__name__)


def json_default(obj):
    """Handle Odoo/Python types that standard json cannot serialize."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return '<binary>'
    return str(obj)


def dumps(value):
    """MCP standard JSON-RPC response formatter."""
    return json.dumps(value, indent=2, default=json_default)


# Bot-gateway-specific helpers (imported lazily to avoid circular imports)
from .bot_auth import validate_bot_api_key, check_rate_limit  # noqa: E402

__all__ = [
    'json_default',
    'dumps',
    'validate_bot_api_key',
    'check_rate_limit',
]
