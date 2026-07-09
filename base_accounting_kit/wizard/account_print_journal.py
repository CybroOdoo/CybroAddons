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


class AccountPrintJournal(models.TransientModel):
    _name = "account.print.journal"
    _inherit = "account.common.journal.report"
    _description = "Account Print Journal"

    name = fields.Char(string="Journal Audit", default="Journal Audit", required=True, translate=True)
    sort_selection = fields.Selection(
        [('date', 'Date'), ('move_name', 'Journal Entry Number')],
        'Entries Sorted by', required=True, default='move_name')
    journal_ids = fields.Many2many('account.journal', string='Journals',
                                   required=True,
                                   default=lambda self: self.env[
                                       'account.journal'].search(
                                       [('type', 'in', ['sale', 'purchase'])]))

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'sort_selection': self.sort_selection})
        return self.env.ref(
            'base_accounting_kit.action_report_journal').with_context(
            landscape=True).report_action(self, data=data)

    def action_print_xlsx(self):
        """Export the journal audit to xlsx."""
        self.ensure_one()
        data = self.pre_print_report(self._xlsx_base_data())
        data['form'].update({'sort_selection': self.sort_selection})
        report_model = self.env[
            'report.base_accounting_kit.report_journal_audit']
        values = report_model._get_report_values(None, data)
        lines = values['lines']
        sum_debit = values['sum_debit']
        sum_credit = values['sum_credit']
        columns = [
            {'label': 'Date', 'width': 12},
            {'label': 'Entry', 'width': 18},
            {'label': 'Account', 'width': 32},
            {'label': 'Partner', 'width': 24},
            {'label': 'Label', 'width': 28},
            {'label': 'Debit', 'width': 16, 'num': True},
            {'label': 'Credit', 'width': 16, 'num': True},
        ]
        rows = []
        for journal in values['docs']:
            rows.append({'cells': [journal.display_name], 'bold': True})
            for aml in lines.get(journal.id, self.env['account.move.line']):
                rows.append({'cells': [
                    str(aml.date or ''), aml.move_id.name or '',
                    '%s %s' % (aml.account_id.code or '',
                               aml.account_id.name or ''),
                    aml.partner_id.name or '', aml.name or '',
                    aml.debit, aml.credit,
                ], 'indent': 1})
            rows.append({'cells': [
                'Total', '', '', '', '', sum_debit(data, journal),
                sum_credit(data, journal),
            ], 'bold': True})
        table = {
            'title': 'Journal Audit',
            'meta': self._xlsx_meta(data['form']),
            'columns': columns,
            'rows': rows,
        }
        return self._xlsx_action('Journal Audit', table)
