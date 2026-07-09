# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class CashFlow(models.Model):
    """Inherits the account.account model to add additional functionality and
     fields to the account"""
    _inherit = 'account.account'

    def get_cash_flow_ids(self):
        """Returns a list of cashflows for the account"""
        cash_flow_id = self.env.ref('base_accounting_kit.account_financial_report_cash_flow0')
        if cash_flow_id:
            return [('parent_id.id', '=', cash_flow_id.id)]

    cash_flow_type = fields.Many2one('account.financial.report',
                                     string="Cash Flow type",
                                     domain=get_cash_flow_ids)

    @api.onchange('cash_flow_type')
    def onchange_cash_flow_type(self):
        """Onchange the cash flow type of the account that will be updating
        the account_ids values"""
        for rec in self.cash_flow_type:
            # update new record
            rec.write({
                'account_ids': [(4, self._origin.id)]
            })
        if self._origin.cash_flow_type.ids:
            for rec in self._origin.cash_flow_type:
                # remove old record
                rec.write({'account_ids': [(3, self._origin.id)]})


class AccountCommonJournalReport(models.TransientModel):
    """Model used for creating the common journal report"""
    _name = 'account.common.journal.report'
    _description = 'Common Journal Report'
    _inherit = "account.common.report"

    amount_currency = fields.Boolean(
        'With Currency',
        help="Print Report with the currency column if the currency differs "
             "from the company currency.")

    def pre_print_report(self, data):
        """Pre-print the given data and that updates the amount
        amount_currency value"""
        data['form'].update({'amount_currency': self.amount_currency})
        return data
