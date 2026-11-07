# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

"""Small helpers shared by the controller and the models."""


def to_bool(value):
    """Convert a stored parameter value to a boolean."""
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return bool(value)


def get_param(env, key, default=False):
    """Read a system parameter straight from the database (no cache)."""
    record = env['ir.config_parameter'].sudo().search(
        [('key', '=', key)], limit=1)
    return record.value if record and record.value else default


def set_param(env, key, value):
    """Write a system parameter. Empty string for off/empty values."""
    value = '' if value in (False, None, 0, '0', 'False', 'false') \
        else str(value)
    env['ir.config_parameter'].sudo().set_str(key, value)