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
"""Reload the Profit and Loss / Balance Sheet structure.

``data/account_financial_report_data.xml`` is a ``noupdate`` file, so a module
upgrade does not apply the corrected report lines (signs, one account type per
line, Equity section). Loading the file in ``init`` mode updates the standard
lines and creates the new ones; lines added by users are left untouched.
"""
import logging

from odoo import api, SUPERUSER_ID
from odoo.tools import convert

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    convert.convert_file(
        env, 'base_accounting_kit',
        'data/account_financial_report_data.xml',
        idref=None, mode='init', noupdate=True)
    _logger.info("base_accounting_kit: financial report structure reloaded.")
