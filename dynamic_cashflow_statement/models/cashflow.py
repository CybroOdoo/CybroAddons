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
from odoo import models


class Cashflow(models.Model):
    """ Class for getting report data """
    _name = "cashflow"
    _description = 'Report advanced cash flows'

    def get_report_values(self, data=None):
        account_res = []
        journal_res = []
        query = """
            SELECT
                aml.account_id,
                aa.name AS account_name,
                SUM(aml.debit) AS total_debit,
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE am.state = 'posted'
            GROUP BY aml.account_id, aa.name
        """
        cr = self._cr
        cr.execute(query)
        rows = cr.dictfetchall()
        grouped_by_code = {}
        for row in rows:
            account = self.env['account.account'].browse(row['account_id'])
            code = account.code or 'N/A'
            grouped_by_code.setdefault(code, {
                'code': code,
                'account_name': row['account_name'],
                'total_debit': 0.0,
                'total_credit': 0.0,
            })
            grouped_by_code[code]['total_debit'] += row['total_debit']
            grouped_by_code[code]['total_credit'] += row['total_credit']
        fetched_data = list(grouped_by_code.values())
        for account in self.env['account.account'].search([]):
            child_lines = self._get_lines(account, data)
            if child_lines:
                account_res.append(child_lines)
        return {
            'fetched_data': fetched_data,
            'journal_res': journal_res,
            'account_res': account_res,
        }

    def _get_lines(self, account, data):
        """ fetch values for lines"""
        user_lang = self.env.user.lang
        # Query to fetch values without date filtration
        query = """SELECT aml.id, aml.move_id, aml.account_id, aj.name ->'%s' as name, am.name as move_name, 
                          SUM(aml.debit) AS total_debit, 
                          SUM(aml.credit) AS total_credit 
                   FROM (
                       SELECT am.* 
                       FROM account_move as am
                       LEFT JOIN account_move_line aml ON aml.move_id = am.id
                       LEFT JOIN account_account aa ON aa.id = aml.account_id
                       WHERE am.state = 'posted'
                   ) am
                   LEFT JOIN account_move_line aml ON aml.move_id = am.id
                   LEFT JOIN account_account aa ON aa.id = aml.account_id
                   LEFT JOIN account_journal aj ON aj.id = am.journal_id
                   WHERE aa.id = %d 
                   GROUP BY aml.id, am.name, aml.account_id, aj.name""" % (user_lang, account.id)
        cr = self._cr
        cr.execute(query)
        fetched_data = cr.dictfetchall()
        # Another query to fetch journal lines without date filtration
        sql = """SELECT aa.name ->'%s' as account_name, aj.id, aj.name ->'%s' as name, 
                          SUM(aml.debit) AS total_debit, 
                          SUM(aml.credit) AS total_credit 
                   FROM (
                       SELECT am.* 
                       FROM account_move as am
                       LEFT JOIN account_move_line aml ON aml.move_id = am.id
                       LEFT JOIN account_account aa ON aa.id = aml.account_id
                       WHERE am.state = 'posted'
                   ) am
                   LEFT JOIN account_move_line aml ON aml.move_id = am.id
                   LEFT JOIN account_account aa ON aa.id = aml.account_id
                   LEFT JOIN account_journal aj ON aj.id = am.journal_id
                   WHERE aa.id = %d
                   GROUP BY aa.name, aj.name, aj.id""" % (account.name, user_lang, account.id)
        cr.execute(sql)
        fetch_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'code': account.code,
                'move_lines': fetched_data,
                'journal_lines': fetch_data,
            }
