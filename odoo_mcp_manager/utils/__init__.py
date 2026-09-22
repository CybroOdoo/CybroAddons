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
import json
import datetime

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
from .bot_auth import validate_bot_api_key, check_rate_limit, secure_compare  # noqa: E402

__all__ = [
    'json_default',
    'dumps',
    'validate_bot_api_key',
    'check_rate_limit',
    'secure_compare',
]
