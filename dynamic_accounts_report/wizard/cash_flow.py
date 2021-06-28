import time
from datetime import datetime

from odoo import models, api, fields
FETCH_RANGE = 2000
import io
import json
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
year = datetime.now().year


class AccountCasgFlow(models.TransientModel):
    _name = "account.cash.flow"
    _inherit = "account.common.report"

    date_from = fields.Date(string="Start Date", default=str(year)+'-01-01')
    date_to = fields.Date(string="End Date", default=fields.Date.today)
    today = fields.Date("Report Date", default=fields.Date.today)
    levels = fields.Selection([('summary', 'Summary'),
                               ('consolidated', 'Consolidated'),
                               ('detailed', 'Detailed'),
                               ('very', 'Very Detailed')],
                              string='Levels', required=True, default='summary',
                              help='Different levels for cash flow statements \n'
                                   'Summary: Month wise report.\n'
                                   'Consolidated: Based on account types.\n'
                                   'Detailed: Based on accounts.\n'
                                   'Very Detailed: Accounts with their move lines')

    account_ids = fields.Many2many(
        "account.account",
        string="Accounts",
    )

    @api.model
    def view_report(self, option):
        r = self.env['account.cash.flow'].search([('id', '=', option[0])])
        data = {
            'model': self,
            'journals': r.journal_ids,
            'target_move': r.target_move,
            'levels': r.levels,
        }
        if r.date_from:
            data.update({
                'date_from': r.date_from,
            })
        if r.date_to:
            data.update({
                'date_to': r.date_to,
            })

        filters = self.get_filter(option)
        report_lines = self._get_report_values(data, option)
        fetched_data = report_lines['fetched_data']
        fetched = report_lines['fetched']
        account_res = report_lines['account_res']
        journal_res = report_lines['journal_res']
        levels = report_lines['levels']
        currency = self._get_currency()

        return {
            'name': "Cash Flow Statements",
            'type': 'ir.actions.client',
            'tag': 'c_f',
            'report_lines': report_lines,
            'fetched_data': fetched_data,
            'fetched': fetched,
            'account_res': account_res,
            'journal_res': journal_res,
            'levels': r.levels,
            'filters': filters,
            'currency': currency,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All']
        if data.get('target_move'):
            filters['target_move'] = data.get('target_move')
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')
        if data.get('levels'):
            filters['levels'] = data.get('levels')

        filters['company_id'] = ''
        filters['accounts_list'] = data.get('accounts_list')
        filters['journals_list'] = data.get('journals_list')
        filters['company_name'] = data.get('company_name')
        filters['target_move'] = data.get('target_move').capitalize()

        return filters

    def get_filter_data(self, option):
        r = self.env['account.cash.flow'].search([('id', '=', option[0])])
        default_filters = {}
        company_id = self.env.company
        company_domain = [('company_id', '=', company_id.id)]
        journals = r.journal_ids if r.journal_ids else self.env['account.journal'].search(company_domain)
        accounts = self.account_ids if self.account_ids else self.env['account.account'].search(company_domain)

        filter_dict = {
            'journal_ids': r.journal_ids.ids,
            'account_ids': self.account_ids.ids,
            'company_id': company_id.id,
            'date_from': r.date_from,
            'date_to': r.date_to,
            'levels': r.levels,
            'target_move': r.target_move,
            'journals_list': [(j.id, j.name, j.code) for j in journals],
            'accounts_list': [(a.id, a.name) for a in accounts],
            'company_name': company_id and company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_values(self, data, option):
        cr = self.env.cr
        data = self.get_filter(option)
        company_id = self.env.company
        currency = company_id.currency_id
        symbol = company_id.currency_id.symbol
        rounding = company_id.currency_id.rounding
        position = company_id.currency_id.position

        fetched_data = []
        account_res = []
        journal_res = []
        fetched = []

        account_type_id = self.env.ref('account.data_account_type_liquidity').id
        model = self.env.context.get('active_model')
        if data.get('levels') == 'summary':
            state = """ WHERE am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
            query3 = """SELECT to_char(am.date, 'Month') as month_part, extract(YEAR from am.date) as year_part,
                         sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                                 sum(aml.balance) AS total_balance FROM (SELECT am.date, am.id, am.state FROM account_move as am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                 WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' ) am
                                             LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                             LEFT JOIN account_account aa ON aa.id = aml.account_id
                                             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                             """ + state + """GROUP BY month_part,year_part"""
            cr = self._cr
            cr.execute(query3)
            fetched_data = cr.dictfetchall()
        elif data.get('date_from') is False:
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get(
                'target_move') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                                sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                                 FROM (SELECT am.* FROM account_move as am
                                                LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                    LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                    LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                    LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                    GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()
        elif data.get('date_from') is False and data.get('date_from') != False:
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get(
                'target_move') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                                           sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                                            FROM (SELECT am.* FROM account_move as am
                                                           LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                           LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                           LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                           WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                               LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                               LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                               LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                               GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()
        elif data.get('date_from') is False and data.get('date_from') != False:
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get(
                'target_move') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                                           sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                                            FROM (SELECT am.* FROM account_move as am
                                                           LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                           LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                           LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                           WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                               LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                               LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                               LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                               GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()

        elif data.get('date_to') == " ":
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get(
                'target_move') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                                sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                                 FROM (SELECT am.* FROM account_move as am
                                                LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                    LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                    LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                    LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                    GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()

        elif data.get('levels') == 'consolidated':
            state = """ WHERE am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
            query2 = """SELECT aat.name, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                         sum(aml.balance) AS total_balance FROM (  SELECT am.id, am.state FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                         WHERE am.date BETWEEN '""" + str(data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' ) am
                                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                                     LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                     """ + state + """GROUP BY aat.name"""
            cr = self._cr
            cr.execute(query2)
            fetched_data = cr.dictfetchall()
        elif data.get('levels') == 'detailed':
            state = """ WHERE am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
            query1 = """SELECT aa.id,aa.name,aa.code, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                         sum(aml.balance) AS total_balance FROM (SELECT am.id, am.state FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                         WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' ) am
                                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                                     LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                     """ + state + """GROUP BY aa.name, aa.code, aa.id"""
            cr = self._cr
            cr.execute(query1)
            fetched_data = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self.get_journal_lines(account, data)
                if child_lines:
                    journal_res.append(child_lines)

        else:
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                             sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                              FROM (SELECT am.* FROM account_move as am
                                             LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                             LEFT JOIN account_account aa ON aa.id = aml.account_id
                                             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                             WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                 LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                 GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self._get_lines(account, data)
                if child_lines:
                    account_res.append(child_lines)
                journals = self.get_journal_lines(account, data)
                if journals:
                    journal_res.append(journals)

        return {
            'date_from': data.get('date_from'),
            'date_to': data.get('date_to'),
            'levels': data.get('level'),
            'doc_ids': self.ids,
            'doc_model': model,
            'fetched_data': fetched_data,
            'account_res': account_res,
            'journal_res': journal_res,
            'fetched': fetched,
            'company_currency_id': currency,
            'company_currency_symbol': symbol,
            'company_currency_position': position,
        }

    def _get_lines(self, account, data):
        account_type_id = self.env.ref(
            'account.data_account_type_liquidity').id
        state = """AND am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
        query = """SELECT aml.account_id,aj.id as j_id,aj.name,am.id, am.name as move_name, sum(aml.debit) AS total_debit, 
                    sum(aml.credit) AS total_credit, COALESCE(SUM(aml.debit - aml.credit),0) AS balance FROM (SELECT am.* FROM account_move as am
                    LEFT JOIN account_move_line aml ON aml.move_id = am.id
                    LEFT JOIN account_account aa ON aa.id = aml.account_id
                    LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                    WHERE am.date BETWEEN '""" + str(
            data.get('date_from')) + """' and '""" + str(
            data.get('date_to')) + """' AND aat.id='""" + str(
            account_type_id) + """' """ + state + """) am
                                        LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                        LEFT JOIN account_account aa ON aa.id = aml.account_id
                                        LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                        WHERE aa.id = """ + str(account.id) + """
                                        GROUP BY am.name, aml.account_id, aj.id, aj.name, am.id"""

        cr = self._cr
        cr.execute(query)
        fetched_data = cr.dictfetchall()

        sql2 = """SELECT aa.name as account_name,aa.id as account_id, aj.id, aj.name, sum(aml.debit) AS total_debit,
                        sum(aml.credit) AS total_credit, sum(aml.balance) AS total_balance FROM (SELECT am.* FROM account_move as am
                            LEFT JOIN account_move_line aml ON aml.move_id = am.id
                            LEFT JOIN account_account aa ON aa.id = aml.account_id
                            LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                            WHERE am.date BETWEEN '""" + str(
            data.get('date_from')) + """' and '""" + str(
            data.get('date_to')) + """' AND aat.id='""" + str(
            account_type_id) + """' """ + state + """) am
                                                LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                                WHERE aa.id = """ + str(
            account.id) + """
                                                GROUP BY aa.name, aj.name, aj.id,aa.id"""

        cr = self._cr
        cr.execute(sql2)
        fetch_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'id': account.id,
                'code': account.code,
                'move_lines': fetched_data,
                'journal_lines': fetch_data,
            }


    def get_journal_lines(self, account, data, offset=0, fetch_range=FETCH_RANGE):
        account_type_id = self.env.ref(
            'account.data_account_type_liquidity').id
        offset_count = offset * fetch_range
        state = """AND am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
        sql2 = """SELECT aa.name as account_name, aj.name, sum(aml.debit) AS total_debit,
         sum(aml.credit) AS total_credit, COALESCE(SUM(aml.debit - aml.credit),0) AS balance FROM (SELECT am.* FROM account_move as am
             LEFT JOIN account_move_line aml ON aml.move_id = am.id
             LEFT JOIN account_account aa ON aa.id = aml.account_id
             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
             WHERE am.date BETWEEN '""" + str(
            data.get('date_from')) + """' and '""" + str(
            data.get('date_to')) + """' AND aat.id='""" + str(
            account_type_id) + """' """ + state + """) am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                 WHERE aa.id = """ + str(account.id) + """
                                 GROUP BY aa.name, aj.name"""

        cr = self._cr
        cr.execute(sql2)
        fetched_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'id': account.id,
                'journal_lines': fetched_data,
                'offset': offset_count,
            }




    @api.model
    def create(self, vals):
        vals['target_move'] = 'posted'
        res = super(AccountCasgFlow, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('target_move'):
            vals.update({'target_move': vals.get('target_move').lower()})
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(6, 0, vals.get('journal_ids'))]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})
        if vals.get('account_ids'):
            vals.update({'account_ids': [(4, j) for j in vals.get('account_ids')]})
        if vals.get('account_ids') == []:
            vals.update({'account_ids': [(5,)]})

        res = super(AccountCasgFlow, self).write(vals)
        return res

    @api.model
    def _get_currency(self):
        journal = self.env['account.journal'].browse(
            self.env.context.get('default_journal_id', False))
        if journal.currency_id:
            return journal.currency_id.id
        lang = self.env.user.lang
        if not lang:
            lang = 'en_US'
        lang = lang.replace("_", '-')
        currency_array = [self.env.company.currency_id.symbol,
                          self.env.company.currency_id.position, lang]
        return currency_array

    def get_dynamic_xlsx_report(self, data, response, report_data, dfr_data):
        report_main_data = json.loads(dfr_data)
        data = json.loads(data)
        report_data = report_main_data.get('report_lines')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        fetched_data = report_data.get('fetched_data')
        account_res = report_data.get('account_res')
        journal_res = report_data.get('journal_res')
        fetched = report_data.get('fetched')
        account_type_id = self.env.ref('account.data_account_type_liquidity').id
        currency_symbol = self.env.company.currency_id.symbol


        logged_users = self.env['res.company']._company_default_get('account.account')
        sheet = workbook.add_worksheet()
        bold = workbook.add_format({'align': 'center',
                                    'bold': True,
                                    'font_size': '10px',
                                    'border': 1})
        date = workbook.add_format({'font_size': '10px'})
        cell_format = workbook.add_format({'bold': True,
                                           'font_size': '10px'})
        head = workbook.add_format({'align': 'center',
                                    'bold': True,
                                    'bg_color': '#D3D3D3',
                                    'font_size': '15px'})
        txt = workbook.add_format({'align': 'left',
                                   'font_size': '10px'})
        txt_left = workbook.add_format({'align': 'left',
                                        'font_size': '10px',
                                        'border': 1})
        txt_center = workbook.add_format({'align': 'center',
                                          'font_size': '10px',
                                          'border': 1})
        amount = workbook.add_format({'align': 'right',
                                      'font_size': '10px',
                                      'border': 1})
        amount_bold = workbook.add_format({'align': 'right',
                                           'bold': True,
                                           'font_size': '10px',
                                           'border': 1})
        txt_bold = workbook.add_format({'align': 'left',
                                        'bold': True,
                                        'font_size': '10px',
                                        'border': 1})

        sheet.set_column('C:C', 30, cell_format)
        sheet.set_column('D:E', 20, cell_format)
        sheet.set_column('F:F', 20, cell_format)
        sheet.merge_range('C3:F5', '')
        sheet.merge_range('C3:F4', 'CASH FLOW STATEMENTS', head)
        sheet.merge_range('C4:F4', '')

        sheet.write('C6', "Date From", cell_format)
        sheet.write('D6', str(data['date_from']), date)
        sheet.write('E6', "Date To", cell_format)
        sheet.write('F6', str(data['date_to']), date)
        if data.get('levels'):
            sheet.write('C7', "Level", cell_format)
            sheet.write('D7', data.get("levels"), date)
        sheet.write('E7', "Target Moves", cell_format)
        sheet.write('F7', data.get("target_move"), date)
        sheet.write('C9', 'NAME', bold)
        sheet.write('D9', 'CASH IN', bold)
        sheet.write('E9', 'CASH OUT', bold)
        sheet.write('F9', 'BALANCE', bold)

        row_num = 9
        col_num = 2
        fetched_data_list = fetched_data
        account_res_list = account_res
        journal_res_list = journal_res
        fetched_list = fetched

        for i_rec in fetched_data_list:
            if data['levels'] == 'summary':
                sheet.write(row_num + 1, col_num, str(i_rec['month_part']) + str(int(i_rec['year_part'])), txt_left)
                sheet.write(row_num + 1, col_num + 1, str(i_rec['total_debit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 2, str(i_rec['total_credit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 3,
                            str(i_rec['total_debit'] - i_rec['total_credit']) + str(currency_symbol),
                            amount)
                row_num = row_num + 1
            elif data['levels'] == 'consolidated':
                sheet.write(row_num + 1, col_num, i_rec['name'], txt_left)
                sheet.write(row_num + 1, col_num + 1, str(i_rec['total_debit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 2, str(i_rec['total_credit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 3,
                            str(i_rec['total_debit'] - i_rec['total_credit']) + str(currency_symbol),
                            amount)
                row_num = row_num + 1

        for j_rec in journal_res_list:
            if data['levels'] == 'detailed':
                for k in fetched_data_list:
                    if k['name'] == j_rec['account']:
                        sheet.write(row_num + 1, col_num, str(k['code']) + str(k['name']), txt_bold)
                        sheet.write(row_num + 1, col_num + 1, str(k['total_debit']) + str(currency_symbol), amount_bold)
                        sheet.write(row_num + 1, col_num + 2, str(k['total_credit']) + str(currency_symbol), amount_bold)
                        sheet.write(row_num + 1, col_num + 3,
                                    str(k['total_debit'] - k['total_credit']) + str(currency_symbol), amount_bold)
                        row_num = row_num + 1
                for l_jrec in j_rec['journal_lines']:
                    sheet.write(row_num + 1, col_num, l_jrec['name'], txt_left)
                    sheet.write(row_num + 1, col_num + 1, str(l_jrec['total_debit']) + str(currency_symbol), amount)
                    sheet.write(row_num + 1, col_num + 2, str(l_jrec['total_credit']) + str(currency_symbol), amount)
                    sheet.write(row_num + 1, col_num + 3,
                                str(l_jrec['total_debit'] - l_jrec['total_credit']) + str(currency_symbol),
                                amount)
                    row_num = row_num + 1

        for j_rec in account_res_list:
            if data['levels'] == 'very':
                for k in fetched_data_list:
                    if k['name'] == j_rec['account']:
                        sheet.write(row_num + 1, col_num, str(k['code']) + str(k['name']), txt_bold)
                        sheet.write(row_num + 1, col_num + 1, str(k['total_debit']) + str(currency_symbol), amount_bold)
                        sheet.write(row_num + 1, col_num + 2, str(k['total_credit']) + str(currency_symbol), amount_bold)
                        sheet.write(row_num + 1, col_num + 3,
                                    str(k['total_debit'] - k['total_credit']) + str(currency_symbol), amount_bold)
                        row_num = row_num + 1
                for l_jrec in j_rec['journal_lines']:
                    if l_jrec['account_name'] == j_rec['account']:
                        sheet.write(row_num + 1, col_num, l_jrec['name'], txt_left)
                        sheet.write(row_num + 1, col_num + 1, str(l_jrec['total_debit']) + str(currency_symbol), amount)
                        sheet.write(row_num + 1, col_num + 2, str(l_jrec['total_credit']) + str(currency_symbol), amount)
                        sheet.write(row_num + 1, col_num + 3,
                                    str(l_jrec['total_debit'] - l_jrec['total_credit']) + str(currency_symbol),
                                    amount)
                        row_num = row_num + 1
                    for m_rec in j_rec['move_lines']:
                        if m_rec['name'] == l_jrec['name']:
                            sheet.write(row_num + 1, col_num, m_rec['move_name'], txt_center)
                            sheet.write(row_num + 1, col_num + 1, str(m_rec['total_debit']) + str(currency_symbol), amount)
                            sheet.write(row_num + 1, col_num + 2, str(m_rec['total_credit']) + str(currency_symbol), amount)
                            sheet.write(row_num + 1, col_num + 3,
                                        str(m_rec['total_debit'] - m_rec['total_credit']) + str(currency_symbol),
                                        amount)
                            row_num = row_num + 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()