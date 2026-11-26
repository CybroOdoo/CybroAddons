# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import time
from odoo import _, api, models
from odoo.exceptions import UserError


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.base_accounting_kit.report_partnerledger'
    """This class extends the functionality of the base Partner Ledger report
        to provide additional features and customization."""

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get the values needed for the Partner Ledger report.
           data: Additional data for the report
           return: Dictionary containing report data"""
        if not data or not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))
        data['computed'] = {}
        data['initial_balances'] = {}
        partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(
            **data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['asset_receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable', 'asset_receivable']

        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.account_type IN %s AND NOT a.deprecated""",
                            (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in
                                           self.env.cr.fetchall()] or [0]
        params = [tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        if data['form']['partner_ids']:
            partner_ids = data['form']['partner_ids']
        else:
            partner_ids = [res['partner_id'] for res in
                           self.env.cr.dictfetchall()]
        partners = partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))
        if data['form']['initial_balance'] and data['form']['partner_ids']:
            # Use ORM domains so dates and ids remain parameters and record
            # rules and company restrictions also apply to opening balances.
            domain = [
                ('partner_id', 'in', partner_ids),
                ('account_id', 'in', data['computed']['account_ids']),
                ('move_id.state', 'in', data['computed']['move_state']),
            ]
            cutoff = data['form'].get('date_from') or data['form'].get('date_to')
            if cutoff:
                domain.append(('date', '<', cutoff))
            if data['form'].get('journal_ids'):
                domain.append(('journal_id', 'in', data['form']['journal_ids']))
            if not data['form']['reconciled']:
                domain.append(('full_reconcile_id', '=', False))
            groups = self.env['account.move.line'].read_group(
                domain, ['partner_id', 'debit:sum', 'credit:sum'],
                ['partner_id'])
            data['initial_balances'] = {
                group['partner_id'][0]: {
                    'debit': group['debit'], 'credit': group['credit'],
                    'balance': group['debit'] - group['credit'],
                } for group in groups
            }
            record = [{
                'name': group['partner_id'][1],
                'initial_debit': group['debit'],
                'initial_credit': group['credit'],
            } for group in groups]
            return {
                'doc_ids': partner_ids,
                'doc_model': self.env['res.partner'],
                'data': data,
                'docs': partners,
                'time': time,
                'lines': self._lines,
                'sum_partner': self._sum_partner,
                'response': record

            }
        else:
            return {
                'doc_ids': partner_ids,
                'doc_model': self.env['res.partner'],
                'data': data,
                'docs': partners,
                'time': time,
                'lines': self._lines,
                'sum_partner': self._sum_partner,
            }
