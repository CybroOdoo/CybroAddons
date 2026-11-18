# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import json
import logging

from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

# Maximum number of products drawn by the out of stock graph.
OUT_OF_STOCK_LIMIT = 100


def check_dashboard_access(env):
    """ Raises an AccessError unless the user is allowed to see the dashboard.

    The dashboard reads the database with SQL queries, which do not apply the
    access rights, so the Inventory user group is checked explicitly.

    :param Environment env: environment of the calling user.
    """
    if not (env.su or env.user.has_group('stock.group_stock_user')):
        raise AccessError(
            env._("You need to be an Inventory user to see the dashboard."))


def localized_name(value, lang=None):
    """ Returns a plain string from a translatable (jsonb) column value.

    :param value: dict of translations, JSON string or plain string.
    :param str lang: preferred language code (for example 'en_US').
    """
    if isinstance(value, str) and value.startswith('{'):
        try:
            value = json.loads(value)
        except ValueError:
            _logger.warning("Could not decode translated name: %s", value)
            return value
    if isinstance(value, dict):
        return (value.get(lang) or value.get('en_US')
                or next(iter(value.values()), ''))
    return value
