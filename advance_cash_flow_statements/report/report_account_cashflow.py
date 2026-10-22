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
#############################################################################
from odoo import api, models


class ReportAccountCashFlow(models.AbstractModel):
    """Abstract model used to generate the Advanced Cash Flow PDF report."""
    _name = "report.advance_cash_flow_statements.cash_flow_pdf_report"
    _description = 'Report advanced cash flows'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare values required for rendering the cash flow PDF report."""
        if not data:
            data = {}

        active_model = self.env.context.get('active_model') or data.get('model') or 'account.wizard'
        doc_ids = docids or data.get('ids') or self.env.context.get('active_ids', [])
        docs = self.env[active_model].browse(doc_ids)

        company = self.env.company
        state_clause = "AND am.state = 'posted'" if data.get('target_move') == 'posted' else "AND am.state != 'cancel'"

        fetched_data = []
        account_res = []
        journal_res = []
        fetched = []

        if data.get('levels') == 'summary':
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
                  AND am.company_id = %s
                  {state_clause}
                GROUP BY month_part, year_part
                ORDER BY year_part, min(am.date)
            """
            self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id))
            raw_data = self.env.cr.dictfetchall()
            for r in raw_data:
                tot_debit = r['total_debit'] or 0.0
                tot_credit = r['total_credit'] or 0.0
                fetched_data.append({
                    'month_part': r['month_part'].strip(),
                    'year_part': int(r['year_part']),
                    'total_debit': tot_debit,
                    'total_credit': tot_credit,
                    'total_balance': tot_debit - tot_credit,
                })

        elif data.get('levels') == 'consolidated':
            query = f"""
                SELECT 
                    aml.account_id,
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE am.date BETWEEN %s AND %s
                  AND am.company_id = %s
                  {state_clause}
                GROUP BY aml.account_id
            """
            self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id))
            raw_data = self.env.cr.dictfetchall()
            for r in raw_data:
                account = self.env['account.account'].browse(r['account_id'])
                code = account.code or ''
                name = account.name or ''
                acc_label = f"{code} {name}".strip() if code else name
                tot_debit = r['total_debit'] or 0.0
                tot_credit = r['total_credit'] or 0.0
                fetched_data.append({
                    'account_id': account.id,
                    'name': acc_label,
                    'total_debit': tot_debit,
                    'total_credit': tot_credit,
                    'total_balance': tot_debit - tot_credit,
                })

        elif data.get('levels') == 'detailed':
            query = f"""
                SELECT 
                    aml.account_id,
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE am.date BETWEEN %s AND %s
                  AND am.company_id = %s
                  {state_clause}
                GROUP BY aml.account_id
            """
            self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id))
            raw_data = self.env.cr.dictfetchall()
            for r in raw_data:
                account = self.env['account.account'].browse(r['account_id'])
                code = account.code or ''
                name = account.name or ''
                tot_debit = r['total_debit'] or 0.0
                tot_credit = r['total_credit'] or 0.0
                fetched_data.append({
                    'account_id': account.id,
                    'code': code,
                    'name': name,
                    'total_debit': tot_debit,
                    'total_credit': tot_credit,
                    'total_balance': tot_debit - tot_credit,
                })
                child_lines = self._get_journal_lines(account, data)
                if child_lines:
                    journal_res.append(child_lines)

        else:  # very detailed
            query = f"""
                SELECT 
                    aml.account_id,
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE am.date BETWEEN %s AND %s
                  AND am.company_id = %s
                  {state_clause}
                GROUP BY aml.account_id
            """
            self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id))
            raw_data = self.env.cr.dictfetchall()
            for r in raw_data:
                account = self.env['account.account'].browse(r['account_id'])
                code = account.code or ''
                name = account.name or ''
                tot_debit = r['total_debit'] or 0.0
                tot_credit = r['total_credit'] or 0.0
                fetched.append({
                    'account_id': account.id,
                    'code': code,
                    'name': name,
                    'total_debit': tot_debit,
                    'total_credit': tot_credit,
                    'total_balance': tot_debit - tot_credit,
                })
                child_lines = self._get_lines(account, data)
                if child_lines:
                    account_res.append(child_lines)

        return {
            'date_from': data.get('date_from'),
            'date_to': data.get('date_to'),
            'levels': data.get('levels'),
            'target_move': data.get('target_move'),
            'today': data.get('today'),
            'logged_users': data.get('logged_users', self.env.user.name),
            'doc_ids': doc_ids,
            'doc_model': active_model,
            'docs': docs,
            'fetched_data': fetched_data,
            'account_res': account_res,
            'journal_res': journal_res,
            'fetched': fetched,
        }

    def _get_lines(self, account, data):
        """Fetch move line and journal-wise totals for a specific account."""
        company = self.env.company
        state_clause = "AND am.state = 'posted'" if data.get('target_move') == 'posted' else "AND am.state != 'cancel'"

        query_moves = f"""
            SELECT 
                aml.account_id,
                am.journal_id,
                am.name as move_name, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            WHERE am.date BETWEEN %s AND %s
              AND am.company_id = %s
              {state_clause}
              AND aml.account_id = %s
            GROUP BY am.name, aml.account_id, am.journal_id
        """
        self.env.cr.execute(query_moves, (data['date_from'], data['date_to'], company.id, account.id))
        move_lines = self.env.cr.dictfetchall()

        query_journals = f"""
            SELECT 
                aj.id as journal_id, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            JOIN account_journal aj ON aj.id = am.journal_id
            WHERE am.date BETWEEN %s AND %s
              AND am.company_id = %s
              {state_clause}
              AND aml.account_id = %s
            GROUP BY aj.id
        """
        self.env.cr.execute(query_journals, (data['date_from'], data['date_to'], company.id, account.id))
        journal_records = self.env.cr.dictfetchall()

        journal_lines = []
        for jr in journal_records:
            journal = self.env['account.journal'].browse(jr['journal_id'])
            journal_lines.append({
                'id': journal.id,
                'name': journal.name,
                'total_debit': jr['total_debit'],
                'total_credit': jr['total_credit'],
            })

        if move_lines:
            return {
                'account_id': account.id,
                'account': account.name,
                'code': account.code or '',
                'move_lines': move_lines,
                'journal_lines': journal_lines,
            }
        return {}

    def _get_journal_lines(self, account, data):
        """Fetch journal-wise debit and credit totals for a specific account."""
        company = self.env.company
        state_clause = "AND am.state = 'posted'" if data.get('target_move') == 'posted' else "AND am.state != 'cancel'"

        query = f"""
            SELECT 
                aj.id as journal_id, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            JOIN account_journal aj ON aj.id = am.journal_id
            WHERE am.date BETWEEN %s AND %s
              AND am.company_id = %s
              {state_clause}
              AND aml.account_id = %s
            GROUP BY aj.id
        """
        self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id, account.id))
        records = self.env.cr.dictfetchall()

        journal_lines = []
        for r in records:
            journal = self.env['account.journal'].browse(r['journal_id'])
            journal_lines.append({
                'id': journal.id,
                'name': journal.name,
                'total_debit': r['total_debit'],
                'total_credit': r['total_credit'],
            })

        if journal_lines:
            return {
                'account_id': account.id,
                'account': account.name,
                'journal_lines': journal_lines,
            }
        return {}
