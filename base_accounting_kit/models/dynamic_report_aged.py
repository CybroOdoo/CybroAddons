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
from odoo import _, fields, models

from .report_company import get_report_branches

ACCOUNT_TYPES = {
    'receivable': ['asset_receivable'],
    'payable': ['liability_payable'],
    'both': ['asset_receivable', 'liability_payable'],
}
# Bucket keys of report_aged_partner._get_partner_move_lines, newest first.
BUCKETS = ('4', '3', '2', '1', '0')


class DynamicAgedPartner(models.AbstractModel):
    """Aged Receivable / Payable: figures from
    ``report_agedpartnerbalance._get_partner_move_lines`` (residual amounts
    as of the date, report company and branches)."""
    _name = 'account.dynamic.report.aged'
    _inherit = 'account.dynamic.report'
    _description = 'Aged Partner Balance'

    _filters = ('date', 'target_move', 'partners')
    _date_mode = 'single'

    def _report_title(self):
        return {'receivable': _("Aged Receivable"),
                'payable': _("Aged Payable")}.get(
            self.env.context.get('aged_account_type'),
            _("Aged Partner Balance"))

    def _option_defs(self):
        return [
            {'key': 'account_type', 'label': _("Accounts"), 'type': 'select',
             'default': 'receivable',
             'values': {'receivable': _("Receivable"),
                        'payable': _("Payable"),
                        'both': _("Receivable and Payable")}},
            {'key': 'period_length', 'label': _("Period Length (days)"),
             'type': 'number', 'default': 30, 'min': 1, 'max': 365},
        ]

    def _company_env(self, options):
        return super()._company_env(options).with_context(
            aged_account_type=options['account_type'])

    @staticmethod
    def _bucket_name(index, period_length):
        """Title of a bucket, with the ranges of the computation: amounts
        due today are "Not due", then 1-30, 31-60, 61-90, 91-120, +120."""
        if index == 0:
            return '+%s' % (4 * period_length)
        return '%s-%s' % ((5 - (index + 1)) * period_length + 1,
                          (5 - index) * period_length)

    def _columns(self, options):
        length = options['period_length']
        return [{'name': _("Not Due"), 'type': 'monetary'}] + [
            {'name': self._bucket_name(int(key), length), 'type': 'monetary'}
            for key in BUCKETS] + [{'name': _("Total"), 'type': 'monetary'}]

    def _aged_data(self, options):
        report = self.env[
            'report.base_accounting_kit.report_agedpartnerbalance']\
            .with_context(company_id=self.env.company.id)
        rows, _total, lines = report._get_partner_move_lines(
            ACCOUNT_TYPES[options['account_type']],
            fields.Date.to_string(options['date_to']),
            options['target_move'], options['period_length'])
        if options['partner_ids']:
            rows = [r for r in rows if r['partner_id'] in options['partner_ids']]
        return rows, lines

    def _lines(self, options):
        rows, _lines = self._aged_data(options)
        lines, totals = [], [0.0] * 7
        for row in rows:
            columns = [row['direction']] + [row[key] for key in BUCKETS] \
                + [row['total']]
            totals = [t + c for t, c in zip(totals, columns)]
            lines.append({'id': 'partner_%s' % (row['partner_id'] or 0),
                          'name': row['name'], 'level': 0,
                          'columns': columns, 'unfoldable': True})
        lines.append({'id': 'total', 'name': _("Total"), 'level': 0,
                      'class': 'total', 'columns': totals})
        return lines

    def _child_lines(self, options, line_id):
        if not line_id.startswith('partner_'):
            return []
        partner_id = int(line_id.split('_')[1]) or False
        _rows, lines = self._aged_data(options)
        children = []
        for item in lines.get(partner_id, []):
            columns = [''] * 7
            # period 6 = not due, period n = bucket key str(n - 1)
            index = 0 if item['period'] == 6 \
                else 1 + BUCKETS.index(str(item['period'] - 1))
            columns[index] = item['amount']
            columns[6] = item['amount']
            line = item['line']
            children.append({
                'id': 'aml_%s' % line.id,
                'name': ' - '.join(str(v) for v in (
                    line.date_maturity or line.date, line.move_id.name,
                    line.name) if v),
                'level': 1, 'parent_id': line_id, 'columns': columns})
        return children

    def _line_action(self, options, line_id):
        if line_id.startswith('aml_'):
            line = self.env['account.move.line'].browse(
                int(line_id.split('_')[1])).exists()
            return line and {
                'type': 'ir.actions.act_window', 'res_model': 'account.move',
                'res_id': line.move_id.id, 'views': [(False, 'form')],
                'target': 'current'}
        if not line_id.startswith('partner_'):
            return False
        partner_id = int(line_id.split('_')[1]) or False
        domain = [
            ('partner_id', '=', partner_id),
            ('account_id.account_type', 'in',
             ACCOUNT_TYPES[options['account_type']]),
            ('date', '<=', fields.Date.to_string(options['date_to'])),
            ('company_id', 'in', get_report_branches(self.env.company).ids),
            ('reconciled', '=', False),
            ('parent_state', 'in', ['posted'] if options['target_move'] ==
             'posted' else ['draft', 'posted']),
        ]
        action = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_account_moves_all')
        action.update({'domain': domain,
                       'context': {'search_default_posted': 0}})
        return action
