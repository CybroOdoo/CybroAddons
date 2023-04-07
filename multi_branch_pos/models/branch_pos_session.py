# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

"""pos session"""

from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class PosSession(models.Model):
    """inherit pos session to add branch field"""
    _inherit = 'pos.session'

    branch_id = fields.Many2one('res.branch', related='config_id.branch_id',
                                string="Branch", readonly=True)

    def _create_account_move(self):
        print("_create_account_move")
        """Create account.move and account.move.line records for the session"""
        journal = self.config_id.journal_id
        # Passing default_journal_id for the calculation of default currency
        # of account move
        # See _get_default_currency in the account/account_move.py.
        account_move = self.env['account.move'].with_context(
            default_journal_id=journal.id).create({
                'journal_id': journal.id,
                'date': fields.Date.context_today(self),
                'ref': self.name,
                'branch_id': self.branch_id.id
            })
        self.write({'move_id': account_move.id})
        print(journal.name)
        data = {}
        data = self._accumulate_amounts(data)
        data = self._create_non_reconciliable_move_lines(data)
        data = self._create_cash_statement_lines_and_cash_move_lines(data)
        data = self._create_invoice_receivable_lines(data)
        data = self._create_stock_output_lines(data)
        data = self._create_balancing_line(data)

        if account_move.line_ids:
            account_move._post()

        data = self._reconcile_account_move_lines(data)
