# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana K P (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models

class ReportAccountCashFlow(models.AbstractModel):
    """  Abstract model used to generate the Advanced Cash Flow PDF report."""
    _name = "report.advance_cash_flow_statements.cash_flow_pdf_report"
    _description = 'Report advanced cash flows'

    @api.model
    def _get_report_values(self, docids, data=None):
        """  Prepare values required for rendering the cash flow PDF report."""
        fetched_data = []
        account_res = []
        journal_res = []
        fetched = []

        active_model = self.env.context.get('active_model')
        docs = self.env[active_model].browse(self.env.context.get('active_id'))

        state_clause = "AND am.state = 'posted'" if data['target_move'] == 'posted' else ''

        if data['levels'] == 'summary':
            query = f"""
                SELECT 
                    to_char(am.date, 'Month') as month_part, 
                    EXTRACT(YEAR FROM am.date) as year_part,
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE am.date BETWEEN %s AND %s
                {state_clause}
                GROUP BY month_part, year_part
            """
            self._cr.execute(query, (data['date_from'], data['date_to']))
            fetched_data = self._cr.dictfetchall()

        elif data['levels'] == 'consolidated':
            query = f"""
                SELECT 
                    aa.name as name, 
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN account_account aa ON aa.id = aml.account_id
                WHERE am.date BETWEEN %s AND %s
                {state_clause}
                GROUP BY aa.name
            """
            self._cr.execute(query, (data['date_from'], data['date_to']))
            fetched_data = self._cr.dictfetchall()

        elif data['levels'] == 'detailed':
            query = f"""
                SELECT 
                    aa.name as name,
                    aa.code_store as code, 
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN account_account aa ON aa.id = aml.account_id
                WHERE am.date BETWEEN %s AND %s
                {state_clause}
                GROUP BY aa.name, aa.code_store
            """
            self._cr.execute(query, (data['date_from'], data['date_to']))
            fetched_data = self._cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self._get_journal_lines(account, data)
                if child_lines:
                    journal_res.append(child_lines)

        else:
            query = f"""
                SELECT 
                    aa.name as name,
                    aa.code_store as code, 
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN account_account aa ON aa.id = aml.account_id
                WHERE am.date BETWEEN %s AND %s
                {state_clause}
                GROUP BY aa.name, aa.code_store
            """
            self._cr.execute(query, (data['date_from'], data['date_to']))
            fetched = self._cr.dictfetchall()

            for account in self.env['account.account'].search([]):
                child_lines = self._get_lines(account, data)
                if child_lines:
                    account_res.append(child_lines)

        # 🔽 FLATTEN DICTIONARIES HERE (before filtering and returning)
        for entry in fetched_data:
            if data['levels'] != 'summary':
                entry['name'] = entry['name']['en_US'] if isinstance(entry['name'], dict) else entry['name']
            if data['levels'] not in ['summary', 'consolidated']:
                entry['code'] = entry['code'].get('1') if isinstance(entry.get('code'), dict) else entry.get('code')

        for i in fetched:
            i['name'] = i['name']['en_US'] if isinstance(i['name'], dict) else i['name']
            i['code'] = i['code'].get('1') if isinstance(i.get('code'), dict) else i.get('code')

        for res in journal_res:
            res['account'] = res['account']['en_US'] if isinstance(res['account'], dict) else res['account']
            for jl in res.get('journal_lines', []):
                jl['account_name'] = jl['account_name']['en_US'] if isinstance(jl['account_name'], dict) else jl[
                    'account_name']
                jl['name'] = jl['name']['en_US'] if isinstance(jl['name'], dict) else jl['name']

        for res in account_res:
            for ml in res.get('move_lines', []):
                ml['name'] = ml['name']['en_US'] if isinstance(ml['name'], dict) else ml['name']
            for jl in res.get('journal_lines', []):
                jl['account_name'] = jl['account_name']['en_US'] if isinstance(jl['account_name'], dict) else jl[
                    'account_name']
                jl['name'] = jl['name']['en_US'] if isinstance(jl['name'], dict) else jl['name']

        # ✅ Filter out incomplete records
        filtered_fetched_data = [entry for entry in fetched_data if None not in entry.values()]

        return {
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'levels': data['levels'],
            'doc_ids': self.ids,
            'doc_model': active_model,
            'docs': docs,
            'fetched_data': filtered_fetched_data,
            'account_res': account_res,
            'journal_res': journal_res,
            'fetched': fetched,
        }

    def _get_lines(self, account, data):
        """  Fetch move line and journal-wise totals for a specific account."""
        state_clause = "AND am.state = 'posted'" if data['target_move'] == 'posted' else ''

        query = f"""
            SELECT 
                aml.account_id,
                aj.name as name, 
                am.name as move_name, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_journal aj ON aj.id = am.journal_id
            WHERE am.date BETWEEN %s AND %s
            {state_clause}
            AND aa.id = %s
            GROUP BY am.name, aml.account_id, aj.name
        """
        self._cr.execute(query, (data['date_from'], data['date_to'], account.id))
        fetched_data = self._cr.dictfetchall()

        query2 = f"""
            SELECT 
                aa.name as account_name, 
                aj.id, 
                aj.name as name, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_journal aj ON aj.id = am.journal_id
            WHERE am.date BETWEEN %s AND %s
            {state_clause}
            AND aa.id = %s
            GROUP BY aa.name, aj.name, aj.id
        """
        self._cr.execute(query2, (data['date_from'], data['date_to'], account.id))
        fetch_data = self._cr.dictfetchall()

        if fetched_data:
            return {
                'account': account.name,
                'code': account.code,
                'move_lines': fetched_data,
                'journal_lines': fetch_data,
            }

    def _get_journal_lines(self, account, data):
        """ Fetch journal-wise debit and credit totals for a specific account."""

        state_clause = "AND am.state = 'posted'" if data['target_move'] == 'posted' else ''

        query = f"""
            SELECT 
                aa.name as account_name, 
                aj.id, 
                aj.name as name, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_journal aj ON aj.id = am.journal_id
            WHERE am.date BETWEEN %s AND %s
            {state_clause}
            AND aa.id = %s
            GROUP BY aa.name, aj.name, aj.id
        """
        self._cr.execute(query, (data['date_from'], data['date_to'], account.id))
        fetched_data = self._cr.dictfetchall()

        if fetched_data:
            return {
                'account': account.name,
                'journal_lines': fetched_data,
            }
