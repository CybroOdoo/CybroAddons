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
from datetime import timedelta

from odoo import fields, models


class DayBookWizard(models.TransientModel):
    _name = 'account.day.book.report'
    _inherit = 'account.report.xlsx.mixin'
    _description = 'Account Day Book Report'

    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 default=lambda self: self.env.company)
    journal_ids = fields.Many2many('account.journal', string='Journals',
                                   required=True,
                                   default=lambda self: self.env[
                                       'account.journal'].search([]))
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')], string='Target Moves', required=True,
                                   default='posted')

    account_ids = fields.Many2many('account.account',
                                   'account_report_daybook_account_rel',
                                   'report_id', 'account_id',
                                   'Accounts')

    date_from = fields.Date(string='Start Date',
                            default=fields.Date.context_today, required=True)
    date_to = fields.Date(string='End Date',
                          default=fields.Date.context_today, required=True)

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form'][
            'journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form'][
            'target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = \
        self.read(['date_from', 'date_to', 'journal_ids', 'target_move',
                   'account_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=self.env.context.get(
                                                'lang') or 'en_US')
        return self.env.ref(
            'base_accounting_kit.day_book_pdf_report').report_action(self,
                                                                     data=data)

    def action_print_xlsx(self):
        """Export the day book to xlsx (entries grouped by date)."""
        self.ensure_one()
        data = {}
        data['form'] = self.read(
            ['date_from', 'date_to', 'journal_ids', 'target_move',
             'account_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context, lang=self.env.context.get('lang') or 'en_US')
        accounts = self.env['account.account'].search(
            [('id', 'in', data['form']['account_ids'])]) \
            if data['form']['account_ids'] \
            else self.env['account.account'].search([])
        report_model = self.env[
            'report.base_accounting_kit.day_book_report_template']
        columns = [
            {'label': 'Date / Account', 'width': 32},
            {'label': 'JRNL', 'width': 8},
            {'label': 'Partner', 'width': 28},
            {'label': 'Ref', 'width': 28},
            {'label': 'Debit', 'width': 16, 'num': True},
            {'label': 'Credit', 'width': 16, 'num': True},
            {'label': 'Balance', 'width': 16, 'num': True},
        ]
        rows = []
        day = self.date_from
        while day <= self.date_to:
            res = report_model.with_context(
                data['form']['used_context'])._get_account_move_entry(
                accounts, data['form'], str(day))
            if res['lines']:
                rows.append({'cells': [
                    str(day), '', '', '', res['debit'], res['credit'],
                    res['balance'],
                ], 'bold': True})
                for line in res['lines']:
                    rows.append({'cells': [
                        line.get('accname') or '', line.get('lcode'),
                        line.get('partner_name') or '',
                        line.get('lname') or '', line.get('debit'),
                        line.get('credit'), line.get('balance'),
                    ], 'indent': 1})
            day += timedelta(days=1)
        table = {
            'title': 'Day Book',
            'meta': self._xlsx_meta(data['form']),
            'columns': columns,
            'rows': rows,
        }
        return self._xlsx_action('Day Book', table)
