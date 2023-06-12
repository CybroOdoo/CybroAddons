# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
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
#############################################################################
"""account bank statement"""
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang


class AccountBankStatement(models.Model):
    """inherit account.bank.statement model to add new branch field"""
    _inherit = 'account.bank.statement'

    branch_id = fields.Many2one('res.branch', string='Branch',
                                help='Branches allowed')

    def _check_balance_end_real_same_as_computed(self):
        """ Check the balance_end_real (encoded manually by the user) is equals
        to the balance_end (computed by odoo).
        In case of a cash statement, the different is set automatically to a
        profit/loss account."""
        for stmt in self:
            if not stmt.currency_id.is_zero(stmt.difference):
                if stmt.journal_type == 'cash':
                    st_line_vals = {
                        'statement_id': stmt.id,
                        'journal_id': stmt.journal_id.id,
                        'amount': stmt.difference,
                        'date': stmt.date,
                        'branch_id': stmt.branch_id.id
                    }
                    if stmt.difference < 0.0:
                        if not stmt.journal_id.loss_account_id:
                            raise UserError(_(
                                'Please go on the %s journal and define a Loss '
                                'Account. This account will be used to record '
                                'cash difference.', stmt.journal_id.name))
                        st_line_vals['payment_ref'] = _(
                            "Cash difference observed during the counting "
                            "(Loss)")
                        st_line_vals['counterpart_account_id'] = \
                            stmt.journal_id.loss_account_id.id
                    else:
                        if not stmt.journal_id.profit_account_id:
                            raise UserError(_(
                                'Please go on the %s journal and define a '
                                'Profit Account. This account will be used to '
                                'record cash difference.',
                                stmt.journal_id.name))
                        st_line_vals['payment_ref'] = _(
                            "Cash difference observed during the counting "
                            "(Profit)")
                        st_line_vals['counterpart_account_id'] = \
                            stmt.journal_id.profit_account_id.id
                    self.env['account.bank.statement.line'].create(st_line_vals)
                else:
                    balance_end_real = formatLang(self.env,
                                                  stmt.balance_end_real,
                                                  currency_obj=stmt.currency_id)
                    balance_end = formatLang(self.env, stmt.balance_end,
                                             currency_obj=stmt.currency_id)
                    raise UserError(_(
                        'The ending balance is incorrect !\nThe expected '
                        'balance (%(real_balance)s) is different from '
                        'the computed one (%(computed_balance)s).',
                        real_balance=balance_end_real,
                        computed_balance=balance_end
                    ))
        return True
