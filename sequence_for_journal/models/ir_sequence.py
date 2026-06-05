# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import datetime

import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class IrSequence(models.Model):
    """inherit ir.sequence to add fields and methods"""
    _inherit = "ir.sequence"

    account_journal_id = fields.Many2one('account.journal',
                                         help="To add the prefix entered in "
                                              "sequence to journal",
                                         string="Journals")

    @api.onchange('prefix')
    def _onchange_prefix(self):
        """change the value in code field in account.journal model when
        value in prefix changed"""
        if not self.account_journal_id:
            return
        self.account_journal_id.code = self.prefix

    def _get_prefix_suffix(self, date=None, date_range=None):
        """Return interpolated prefix/suffix with extra month text tokens."""

        def _interpolate(string, values):
            return (string % values) if string else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(
                pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(
                    date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(
                    date_range or self._context.get('ir_sequence_date_range'))

            sequences = {
                'year': '%Y', 'month': '%m', 'month_name': '%B',
                'month_abbr': '%b', 'day': '%d', 'y': '%y', 'doy': '%j',
                'woy': '%W', 'weekday': '%w', 'h24': '%H', 'h12': '%I',
                'min': '%M', 'sec': '%S',
            }
            values = {}
            for key, date_format in sequences.items():
                values[key] = effective_date.strftime(date_format)
                values['range_' + key] = range_date.strftime(date_format)
                values['current_' + key] = now.strftime(date_format)
            return values

        self.ensure_one()
        values = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, values)
            interpolated_suffix = _interpolate(self.suffix, values)
        except (KeyError, ValueError, TypeError):
            raise UserError(_('Invalid prefix or suffix for sequence "%s"',
                              self.name))
        return interpolated_prefix, interpolated_suffix
