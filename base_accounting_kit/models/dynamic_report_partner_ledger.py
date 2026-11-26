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
    'customer': ['asset_receivable'],
    'supplier': ['liability_payable'],
    'customer_supplier': ['asset_receivable', 'liability_payable'],
}


class DynamicPartnerLedger(models.AbstractModel):
    """Partner Ledger: figures from ``report_partnerledger._partner_data``
    (opening balance, running balance, grand total)."""
    _name = 'account.dynamic.report.partner_ledger'
    _inherit = 'account.dynamic.report'
    _description = 'Partner Ledger'

    _filters = ('date', 'target_move', 'journals', 'partners', 'analytic')

    def _report_title(self):
        return _("Partner Ledger")

    def _option_defs(self):
        return [
            {'key': 'result_selection', 'label': _("Partner's"),
             'type': 'select', 'default': 'customer',
             'values': {'customer': _("Receivable Accounts"),
                        'supplier': _("Payable Accounts"),
                        'customer_supplier':
                            _("Receivable and Payable Accounts")}},
            {'key': 'reconciled', 'label': _("Reconciled Entries"),
             'type': 'bool', 'default': True},
            {'key': 'amount_currency', 'label': _("With Currency"),
             'type': 'bool', 'default': False},
        ]

    def _columns(self, options):
        columns = [{'name': _("Initial Balance"), 'type': 'monetary'},
                   {'name': _("Debit"), 'type': 'monetary'},
                   {'name': _("Credit"), 'type': 'monetary'},
                   {'name': _("Balance"), 'type': 'monetary'}]
        if options['amount_currency']:
            columns.append({'name': _("Amount Currency"), 'type': 'text'})
        return columns

    def _ledger_data(self, options, partner_ids=None):
        """The kit computation, with the options as its ``data``."""
        types = ACCOUNT_TYPES[options['result_selection']]
        accounts = self.env['account.account'].search([
            ('account_type', 'in', types),
            *self.env['account.account']._check_company_domain(
                self.env.company)])
        ctx = self._report_context(options)
        if partner_ids:
            ctx['partner_ids'] = self.env['res.partner'].browse(partner_ids)
        data = {
            'form': {'reconciled': options['reconciled'],
                     'amount_currency': options['amount_currency'],
                     'used_context': ctx},
            'computed': {
                'move_state': ['posted'] if options['target_move'] ==
                'posted' else ['draft', 'posted'],
                'ACCOUNT_TYPE': types,
                'account_ids': accounts.ids,
            },
        }
        return self.env['report.base_accounting_kit.report_partnerledger']\
            ._partner_data(data)

    def _lines(self, options):
        partners, partner_data, grand_total = self._ledger_data(options)
        extra = [''] if options['amount_currency'] else []
        lines = []
        for partner in partners:
            values = partner_data[partner.id]
            init = values['initial'] or {'debit': 0.0, 'credit': 0.0,
                                         'balance': 0.0}
            lines.append({
                'id': 'partner_%s' % partner.id,
                'name': partner.display_name,
                'level': 0,
                'columns': [init['balance'], values['debit'] - init['debit'],
                            values['credit'] - init['credit'],
                            values['balance']] + extra,
                'unfoldable': True,
            })
        initial = sum((partner_data[p.id]['initial'] or {}).get('balance', 0.0)
                      for p in partners)
        lines.append({'id': 'total', 'name': _("Total"), 'level': 0,
                      'class': 'total',
                      'columns': [initial, grand_total['debit'] - sum(
                          (partner_data[p.id]['initial'] or {}).get(
                              'debit', 0.0) for p in partners),
                          grand_total['credit'] - sum(
                              (partner_data[p.id]['initial'] or {}).get(
                                  'credit', 0.0) for p in partners),
                          grand_total['balance']] + extra})
        return lines

    def _child_lines(self, options, line_id):
        if not line_id.startswith('partner_'):
            return []
        partner_id = int(line_id.split('_')[1])
        _partners, partner_data, _total = self._ledger_data(
            options, [partner_id])
        values = partner_data.get(partner_id)
        if not values:
            return []
        lines = []
        if values['initial']:
            lines.append({
                'id': 'init_%s' % partner_id, 'name': _("Initial Balance"),
                'level': 1, 'parent_id': line_id,
                'columns': ['', values['initial']['debit'],
                            values['initial']['credit'],
                            values['initial']['balance']]
                + ([''] if options['amount_currency'] else [])})
        for item in values['lines']:
            columns = ['', item['debit'], item['credit'], item['progress']]
            if options['amount_currency']:
                columns.append('%s %s' % (item['amount_currency'],
                                          item['currency_id'].symbol or '')
                               if item['currency_id'] else '')
            lines.append({
                'id': 'aml_%s' % item['id'],
                'name': ' - '.join(str(v) for v in (
                    item['date'], item['code'], item['a_name'],
                    item['displayed_name']) if v),
                'level': 1, 'parent_id': line_id, 'columns': columns})
        return lines

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
        partner = self.env['res.partner'].browse(
            int(line_id.split('_')[1])).exists()
        if not partner:
            return False
        domain = [
            ('partner_id', '=', partner.id),
            ('account_id.account_type', 'in',
             ACCOUNT_TYPES[options['result_selection']]),
            ('date', '>=', fields.Date.to_string(options['date_from'])),
            ('date', '<=', fields.Date.to_string(options['date_to'])),
            ('company_id', 'in', get_report_branches(self.env.company).ids),
            ('parent_state', 'in', ['posted'] if options['target_move'] ==
             'posted' else ['draft', 'posted']),
        ]
        action = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_account_moves_all')
        action.update({'name': partner.display_name, 'domain': domain,
                       'context': {'search_default_posted': 0}})
        return action
