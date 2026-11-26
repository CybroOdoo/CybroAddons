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
"""Asset boards no longer hold future draft entries.

Before 20.0.2.3.0, computing a board created a draft entry for every line at
once. Now each entry is created and posted when its line comes due. Delete
the draft depreciation entries and free their board lines (and the lines of
cancelled entries); the daily cron creates the due ones again. Posted entries
are not touched. Every deleted entry is noted on its asset.

Older versions also posted ungrouped depreciation entries with 0.00 amounts.
Those posted entries are only reported (asset chatter and log), not changed.
"""
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def _report_zero_entries(env):
    """Note on each asset its posted depreciation entries without amount."""
    lines = env['account.asset.depreciation.line'].search([
        ('move_id.state', '=', 'posted'), ('amount', '!=', 0)])
    zero = lines.filtered(lambda l: l.move_id.currency_id.is_zero(
        sum(l.move_id.line_ids.mapped('debit'))))
    by_asset = {}
    for line in zero:
        by_asset.setdefault(line.asset_id, []).append(
            '%s (%s, %s)' % (line.move_id.display_name, line.depreciation_date,
                             line.amount))
    for asset, names in by_asset.items():
        asset.message_post(body=env._(
            "Upgrade check: these posted depreciation entries have no "
            "amount (0.00), so the depreciation is missing in the books: %s",
            ', '.join(names)))
    if zero:
        _logger.warning("%d posted depreciation entries have no amount, on %d "
                        "assets (see the assets' chatter).",
                        len(zero), len(by_asset))


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _report_zero_entries(env)
    lines = env['account.asset.depreciation.line'].search([
        ('move_id', '!=', False), ('move_id.state', '!=', 'posted')])
    if not lines:
        return
    drafts = lines.move_id.filtered(lambda m: m.state == 'draft')
    by_asset = {}
    for line in lines.filtered(lambda l: l.move_id in drafts):
        by_asset.setdefault(line.asset_id, []).append(
            '%s (%s, %s)' % (line.move_id.display_name, line.depreciation_date,
                             line.amount))
    lines.write({'move_id': False})
    drafts.with_context(force_delete=True).unlink()
    for asset, names in by_asset.items():
        asset.message_post(body=env._(
            "Upgrade: draft depreciation entries deleted, they are created "
            "again when due: %s", ', '.join(names)))
    _logger.info("Deleted %d draft depreciation entries, freed %d board lines.",
                 len(drafts), len(lines))
