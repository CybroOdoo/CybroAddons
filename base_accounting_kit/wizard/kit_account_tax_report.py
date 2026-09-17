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


class AccountTaxReport(models.TransientModel):
    _name = 'kit.account.tax.report'
    _inherit = "account.common.report"
    _description = 'Tax Report'

    name = fields.Char(string="Tax Report", default="Tax Report",
                       required=True, translate=True)

    def _print_report(self, data):
        return self.env.ref(
            'base_accounting_kit.action_report_account_tax').report_action(
            self, data=data)

    def action_print_xlsx(self):
        """Export the tax report to xlsx."""
        self.ensure_one()
        data = self._xlsx_base_data()
        groups = self.env[
            'report.base_accounting_kit.report_tax'].get_lines(data['form'])
        columns = [
            {'label': 'Tax', 'width': 45},
            {'label': 'Net', 'width': 18, 'num': True},
            {'label': 'Tax Amount', 'width': 18, 'num': True},
        ]
        rows = []
        for section, label in (('sale', 'Sales'), ('purchase', 'Purchases')):
            if groups.get(section):
                rows.append({'cells': [label], 'bold': True})
                for tax in groups[section]:
                    rows.append({'cells': [
                        tax['name'], tax.get('net', 0.0), tax.get('tax', 0.0),
                    ], 'indent': 1})
        table = {
            'title': 'Tax Report',
            'meta': self._xlsx_meta(data['form']),
            'columns': columns,
            'rows': rows,
        }
        return self._xlsx_action('Tax Report', table)
