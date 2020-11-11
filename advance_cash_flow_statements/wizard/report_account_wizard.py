# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, api


class ReportAccountWizard(models.AbstractModel):
    _name = "report.advance_cash_flow_statements.cash_flow_pdf_report"

    @api.model
    def _get_report_values(self, docids, data=None):
        fetched_data = []
        account_res = []
        journal_res = []
        fetched = []
        account_type_id = self.env.ref('account.data_account_type_liquidity').id
        active_model = self.env.context.get('active_model')
        docs = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        if data['levels'] == 'summary':
            state = """ WHERE am.state = 'posted' """ if data['target_move'] == 'posted' else ''
            query3 = """SELECT to_char(am.date, 'Month') as month_part, extract(YEAR from am.date) as year_part,
             sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                     sum(aml.balance) AS total_balance FROM (SELECT am.date, am.id, am.state FROM account_move as am
                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                     LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                     WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
                data['date_to']) + """' ) am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                 """ + state + """GROUP BY month_part,year_part"""
            cr = self._cr
            cr.execute(query3)
            fetched_data = cr.dictfetchall()
        elif data['levels'] == 'consolidated':
            state = """ WHERE am.state = 'posted' """ if data['target_move'] == 'posted' else ''
            query2 = """SELECT aat.name, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
             sum(aml.balance) AS total_balance FROM (  SELECT am.id, am.state FROM account_move as am
             LEFT JOIN account_move_line aml ON aml.move_id = am.id
             LEFT JOIN account_account aa ON aa.id = aml.account_id
             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
             WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
                data['date_to']) + """' ) am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                         """ + state + """GROUP BY aat.name"""
            cr = self._cr
            cr.execute(query2)
            fetched_data = cr.dictfetchall()
        elif data['levels'] == 'detailed':
            state = """ WHERE am.state = 'posted' """ if data['target_move'] == 'posted' else ''
            query1 = """SELECT aa.name,aa.code, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
             sum(aml.balance) AS total_balance FROM (SELECT am.id, am.state FROM account_move as am
             LEFT JOIN account_move_line aml ON aml.move_id = am.id
             LEFT JOIN account_account aa ON aa.id = aml.account_id
             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
             WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
                data['date_to']) + """' ) am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                         """ + state + """GROUP BY aa.name, aa.code"""
            cr = self._cr
            cr.execute(query1)
            fetched_data = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self._get_journal_lines(account, data)
                if child_lines:
                    journal_res.append(child_lines)

        else:
            account_type_id = self.env.ref('account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data['target_move'] == 'posted' else ''
            sql = """SELECT DISTINCT aa.name,aa.code, sum(aml.debit) AS total_debit,
                         sum(aml.credit) AS total_credit FROM (SELECT am.* FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                         WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
                data['date_to']) + """'  """ + state + """) am
                                             LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                             LEFT JOIN account_account aa ON aa.id = aml.account_id
                                             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                             GROUP BY aa.name, aa.code"""
            cr = self._cr
            cr.execute(sql)
            fetched = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self._get_lines(account, data)
                if child_lines:
                    account_res.append(child_lines)

        return {
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'levels': data['levels'],
            'doc_ids': self.ids,
            'doc_model': active_model,
            'docs': docs,
            'fetched_data': fetched_data,
            'account_res': account_res,
            'journal_res': journal_res,
            'fetched': fetched,
        }

    def _get_lines(self, account, data):
        account_type_id = self.env.ref('account.data_account_type_liquidity').id
        state = """AND am.state = 'posted' """ if data['target_move'] == 'posted' else ''
        query = """SELECT aml.account_id,aj.name, am.name as move_name, sum(aml.debit) AS total_debit, 
             sum(aml.credit) AS total_credit FROM (SELECT am.* FROM account_move as am
             LEFT JOIN account_move_line aml ON aml.move_id = am.id
             LEFT JOIN account_account aa ON aa.id = aml.account_id
             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
             WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
            data['date_to']) + """' """ + state + """) am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                 WHERE aa.id = """ + str(account.id) + """
                                 GROUP BY am.name, aml.account_id, aj.name"""

        cr = self._cr
        cr.execute(query)
        fetched_data = cr.dictfetchall()
        sql2 = """SELECT aa.name as account_name, aj.id, aj.name, sum(aml.debit) AS total_debit,
                 sum(aml.credit) AS total_credit FROM (SELECT am.* FROM account_move as am
                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                     LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                     WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
            data['date_to']) + """' """ + state + """) am
                                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                                         LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                         WHERE aa.id = """ + str(account.id) + """
                                         GROUP BY aa.name, aj.name, aj.id"""

        cr = self._cr
        cr.execute(sql2)
        fetch_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'code': account.code,
                'move_lines': fetched_data,
                'journal_lines': fetch_data,
            }

    def _get_journal_lines(self, account, data):
        account_type_id = self.env.ref('account.data_account_type_liquidity').id
        state = """AND am.state = 'posted' """ if data['target_move'] == 'posted' else ''
        sql2 = """SELECT aa.name as account_name, aj.id, aj.name, sum(aml.debit) AS total_debit,
         sum(aml.credit) AS total_credit FROM (SELECT am.* FROM account_move as am
             LEFT JOIN account_move_line aml ON aml.move_id = am.id
             LEFT JOIN account_account aa ON aa.id = aml.account_id
             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
             WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
            data['date_to']) + """'  """ + state + """) am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                 WHERE aa.id = """ + str(account.id) + """
                                 GROUP BY aa.name, aj.name, aj.id"""

        cr = self._cr
        cr.execute(sql2)
        fetched_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'journal_lines': fetched_data,
            }
