# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class AccountPartnerLedger(models.TransientModel):
    """This wizard allows users to generate a Partner Ledger report
        with various options."""
    _inherit = "account.report.partner.ledger"

    partner_ids = fields.Many2many('res.partner', 'partner_ledger_partner_rel',
                                   'id', 'partner_id', string='Partners',
                                   help='Select specific partners for the '
                                        'ledger report.')
    is_include_initial_balance = fields.Boolean(
        string='Include Initial & closing Balance',
        help='Check this box to include initial and closing balances in the'
             'report.')

    def _print_report(self, data):
        """Prepare and print the Partner Ledger report.This method updates
        the report data with the selected options and triggers the
        report action.
        data: The report data.
        return: The report action."""
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency,
                             'partner_ids': self.partner_ids.ids,
                             'initial_balance': self.is_include_initial_balance})
        return self.env.ref(
            'base_accounting_kit.action_report_partnerledger').report_action(
            self, data=data)
