# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ijaz Ahammed, Varsha Vivek (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import time
import datetime
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ReportFinancial(models.AbstractModel):
    _name = 'report.cash_flow_statement.report_financial'

    def _compute_account_balance(self, accounts):
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of credit or debit
                cash_in_operation = self.env.ref('cash_flow_statement.cash_in_from_operation0')
                cash_out_operation = self.env.ref('cash_flow_statement.cash_out_operation1')
                cash_in_financial = self.env.ref('cash_flow_statement.cash_in_financial0')
                cash_out_financial = self.env.ref('cash_flow_statement.cash_out_financial1')
                cash_in_investing = self.env.ref('cash_flow_statement.cash_in_investing0')
                cash_out_investing = self.env.ref('cash_flow_statement.cash_out_investing1')

                res[report.id]['account'] = self._compute_account_balance(report.parent_id.account_ids)

                for value in res[report.id]['account'].values():
                    if report == cash_in_operation or report == cash_in_financial or report == cash_in_investing:
                        res[report.id]['debit'] += value['debit']
                        res[report.id]['balance'] += value['debit']
                    elif report == cash_out_operation or report == cash_out_financial or report == cash_out_investing:
                        res[report.id]['credit'] += value['credit']
                        res[report.id]['balance'] += -(value['credit'])

            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked
                res[report.id]['account'] = self._compute_account_balance(report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)

            elif report.type == 'sum':
                # it's the sum of the child records
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value.get(field)
        return res

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)

        for report in child_reports:
            vals = {
                'name': report.name,
                'id': report.id,
                'balance': res[report.id]['balance'] * report.sign,
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False,  # used to underline the financial report balances,
                'debit': res[report.id]['debit'],
                'credit': res[report.id]['credit']
            }

            lines.append(vals)
            if report.display_detail == 'no_detail':
                # the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if res[report.id].get('account'):
                cash_in_operation = self.env.ref('cash_flow_statement.cash_in_from_operation0')
                cash_out_operation = self.env.ref('cash_flow_statement.cash_out_operation1')
                cash_in_financial = self.env.ref('cash_flow_statement.cash_in_financial0')
                cash_out_financial = self.env.ref('cash_flow_statement.cash_out_financial1')
                cash_in_investing = self.env.ref('cash_flow_statement.cash_in_investing0')
                cash_out_investing = self.env.ref('cash_flow_statement.cash_out_investing1')

                if report == cash_in_operation or report == cash_in_financial or report == cash_in_investing:
                    sub_lines = []
                    for account_id, value in res[report.id]['account'].items():

                        flag = False
                        account = self.env['account.account'].browse(account_id)
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'id': account.id,
                            'balance': value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                            'cash_flow_type': account.cash_flow_type.id,
                            'debit': value['debit'],
                            'credit': value['credit']
                        }

                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                        if not account.company_id.currency_id.is_zero(vals['balance']):
                            flag = True

                        if flag:
                            if vals['debit'] != 0:
                                vals['credit'] = 0
                                vals['balance'] = vals['debit']
                                sub_lines.append(vals)
                    lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
                elif report == cash_out_operation or report == cash_out_financial or report == cash_out_investing:
                    sub_lines = []
                    for account_id, value in res[report.id]['account'].items():

                        flag = False
                        account = self.env['account.account'].browse(account_id)
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'id': account.id,
                            'balance': value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                            'cash_flow_type': account.cash_flow_type.id,
                            'debit': value['debit'],
                            'credit': value['credit']
                        }

                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                        if not account.company_id.currency_id.is_zero(vals['balance']):
                            flag = True
                        if flag:
                            if vals['credit'] != 0:
                                vals['debit'] = 0
                                vals['balance'] = -(vals['credit'])
                                sub_lines.append(vals)

                    lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines

    def find_cash_at_beginning(self, form):
        cr = self.env.cr
        accounts = self.env['account.account'].search([('cash_flow_type', '!=', False)])
        account_ids = []
        for account in accounts:
            account_ids.append(account['id'])

        sum_deb = 0
        sum_cred = 0
        sum_bal = 0
        for acnt in account_ids:
            query = "SELECT sum(debit) as debit,sum(credit) as credit, sum(debit) - sum(credit)" \
                    "balance from account_move_line aml where aml.account_id = %s"
            vals = []

            if form['date_from']:
                query += " and aml.date<%s"
                vals += [acnt, form['date_from']]
            else:
                vals += [acnt]
            cr.execute(query, tuple(vals))
            values = cr.dictfetchall()

            for vals in values:
                if vals['balance']:
                    sum_deb += vals['debit']
                    sum_cred += vals['credit']
                    sum_bal += vals['balance']

        return sum_deb,sum_cred,sum_bal

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        end_date = []
        if data['form']['date_from']:
            from_date = datetime.datetime.strptime(data['form']['date_from'], '%Y-%m-%d').date()
            end_date = from_date - (datetime.timedelta(days=1))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        report_lines = self.get_account_lines(data.get('form'))
        cash_beginning = self.find_cash_at_beginning(data.get('form'))
        print('cash_beginning', cash_beginning[2])

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_account_lines': report_lines,
            'end_date': end_date,
            'sum_deb': cash_beginning[0],
            'sum_cred': cash_beginning[1],
            'sum_bal': cash_beginning[2],
        }


class CashFlow(models.Model):
    _inherit = 'account.account'

    def get_cash_flow_ids(self):
        cash_flow_id = self.env.ref('cash_flow_statement.account_financial_report_cash_flow0')
        if cash_flow_id:
            return [('parent_id.id', '=', cash_flow_id.id)]

    cash_flow_type = fields.Many2one('account.financial.report', string="Cash Flow type", domain=get_cash_flow_ids)

    @api.onchange('cash_flow_type')
    def onchange_cash_flow_type(self):

        for rec in self.cash_flow_type:
            # update new record
            rec.write({
                'account_ids': [(4, self._origin.id)]
            })

        if self._origin.cash_flow_type.ids:
            for rec in self._origin.cash_flow_type:
                # remove old record
                rec.write({
                    'account_ids': [(3, self._origin.id)]
                })
