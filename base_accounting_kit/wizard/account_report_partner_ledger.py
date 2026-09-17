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
from odoo import fields, models


class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _inherit = "account.common.partner.report"
    _description = "Account Partner Ledger"

    name = fields.Char(string="Partner Ledger Report", default="Partner Ledger Report", required=True, translate=True)
    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on report if the "
                                          "currency differs from the company currency.")
    reconciled = fields.Boolean('Reconciled Entries')

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency})
        return self.env.ref(
            'base_accounting_kit.action_report_partnerledger').report_action(
            self, data=data)

    def action_print_xlsx(self):
        """Export the partner ledger to xlsx."""
        self.ensure_one()
        data = self.pre_print_report(self._xlsx_base_data())
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency})
        report_model = self.env[
            'report.base_accounting_kit.report_partnerledger']
        values = report_model._get_report_values(None, data)
        lines_fn = values['lines']
        columns = [
            {'label': 'Date', 'width': 12},
            {'label': 'JRNL', 'width': 8},
            {'label': 'Account', 'width': 28},
            {'label': 'Ref', 'width': 32},
            {'label': 'Debit', 'width': 16, 'num': True},
            {'label': 'Credit', 'width': 16, 'num': True},
            {'label': 'Balance', 'width': 16, 'num': True},
        ]
        rows = []
        for partner in values['docs']:
            rows.append({'cells': [partner.name], 'bold': True})
            for line in lines_fn(data, partner):
                rows.append({'cells': [
                    line.get('date'), line.get('code'),
                    line.get('a_name') or '', line.get('displayed_name') or '',
                    line.get('debit'), line.get('credit'),
                    line.get('progress'),
                ], 'indent': 1})
        table = {
            'title': 'Partner Ledger',
            'meta': self._xlsx_meta(data['form']),
            'columns': columns,
            'rows': rows,
        }
        return self._xlsx_action('Partner Ledger', table)
