import time
from odoo import fields, models, api

import io
import json
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class TrialView(models.TransientModel):
    _inherit = "account.common.report"
    _name = 'account.trial.balance'

    journal_ids = fields.Many2many('account.journal',

                                   string='Journals', required=True,
                                   default=[])
    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')

    # target_move = fields.Selection([('posted', 'All Posted Entries'),
    #                                 ('all', 'All Entries')],
    #                                string='Target Moves', required=True)

    @api.model
    def view_report(self, option):
        r = self.env['account.trial.balance'].search([('id', '=', option[0])])

        data = {
            'display_account': r.display_account,
            'model':self,
            'journals': r.journal_ids,
            'target_move': r.target_move,

        }
        if r.date_from:
            data.update({
                'date_from':r.date_from,
            })
        if r.date_to:
            data.update({
                'date_to':r.date_to,
            })

        filters = self.get_filter(option)
        records = self._get_report_values(data)
        currency = self._get_currency()

        return {
            'name': "Trial Balance",
            'type': 'ir.actions.client',
            'tag': 't_b',
            'filters': filters,
            'report_lines': records['Accounts'],
            'debit_total': records['debit_total'],
            'credit_total': records['credit_total'],
            'currency': currency,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('target_move'):
            filters['target_move'] = data.get('target_move')
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')

        filters['company_id'] = ''
        filters['journals_list'] = data.get('journals_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def get_filter_data(self, option):
        r = self.env['account.trial.balance'].search([('id', '=', option[0])])
        default_filters = {}
        company_id = r.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        journals = r.journal_ids if r.journal_ids else self.env['account.journal'].search(company_domain)

        filter_dict = {
            'journal_ids': r.journal_ids.ids,
            'company_id': company_id.id,
            'date_from': r.date_from,
            'date_to': r.date_to,
            'target_move': r.target_move,
            'journals_list': [(j.id, j.name, j.code) for j in journals],
            'company_name': company_id and company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_values(self, data):
        docs = data['model']
        display_account = data['display_account']
        journals = data['journals']
        accounts = self.env['account.account'].search([])
        account_res = self._get_accounts(accounts, display_account, data)
        debit_total = 0
        debit_total = sum(x['debit'] for x in account_res)
        credit_total = sum(x['credit'] for x in account_res)
        return {
            'doc_ids': self.ids,
            'debit_total': debit_total,
            'credit_total': credit_total,
            'docs': docs,
            'time': time,
            'Accounts': account_res,
        }

    @api.model
    def create(self, vals):
        vals['target_move'] = 'all'
        res = super(TrialView, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(6, 0, vals.get('journal_ids'))]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})
        res = super(TrialView, self).write(vals)
        return res

    def _get_accounts(self, accounts, display_account, data):

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line LEFT JOIN account_move AS account_move_line__move_id ON (account_move_line.move_id = account_move_line__move_id.id) JOIN account_journal jrnl ON (account_move_line.journal_id=jrnl.id)'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        if data['target_move'] == 'posted':
            filters += " AND account_move_line__move_id.state = 'posted'"
        else:
            filters += " AND account_move_line__move_id.state in ('draft','posted')"
        if data.get('date_from'):
            filters += " AND account_move_line.date >= '%s'" % data.get('date_from')
        if data.get('date_to'):
            filters += " AND account_move_line.date <= '%s'" % data.get('date_to')

        if data['journals']:
            filters += ' AND jrnl.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
        # tables += ' JOIN account_journal jrnl ON (account_move_line.journal_id=jrnl.id)'
        # compute the balance, debit and credit for the provided accounts
        request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            res['id'] = account.id
            if data.get('date_from'):

                res['Init_balance'] = self.get_init_bal(account, display_account, data)

            if account.id in account_result:
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(
                    res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (
                    not currency.is_zero(res['debit']) or not currency.is_zero(
                    res['credit'])):
                account_res.append(res)
        return account_res

    def get_init_bal(self, account, display_account, data):
        if data.get('date_from'):

            tables, where_clause, where_params = self.env[
                'account.move.line']._query_get()
            tables = tables.replace('"', '')
            if not tables:
                tables = 'account_move_line'
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            tables += ' JOIN account_move am ON (account_move_line.move_id=am.id)'
            if data['target_move'] == 'posted':
                filters += " AND am.state = 'posted'"
            else:
                filters += " AND am.state in ('draft','posted')"
            if data.get('date_from'):
                filters += " AND account_move_line.date < '%s'" % data.get('date_from')

            if data['journals']:
                filters += ' AND jrnl.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
            tables += ' JOIN account_journal jrnl ON (account_move_line.journal_id=jrnl.id)'

            # compute the balance, debit and credit for the provided accounts
            request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id = %s" % account.id + filters + " GROUP BY account_id")
            params = tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                return row

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
                          self.env.company.currency_id.position,
                          lang]
        return currency_array

    def get_dynamic_xlsx_report(self, data, response ,report_data, dfr_data):
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        total = json.loads(dfr_data)
        filters = json.loads(data)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_l = workbook.add_format({'font_size': '10px', 'border': 1, 'bold': True})
        sheet.merge_range('A2:D3', self.env.user.company_id.name + ':' + ' Trial Balance', head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})
        if filters.get('date_from'):
            sheet.merge_range('A4:B4', 'From: '+filters.get('date_from') , date_head)
        if filters.get('date_to'):
            sheet.merge_range('C4:D4', 'To: '+ filters.get('date_to'), date_head)
        sheet.merge_range('A5:D6', 'Journals: ' + ', '.join([ lt or '' for lt in filters['journals'] ]) + '  Target Moves: '+ filters.get('target_move'), date_head)
        sheet.write('A7', 'Code', sub_heading)
        sheet.write('B7', 'Amount', sub_heading)
        if filters.get('date_from'):
            sheet.write('C7', 'Initial Debit', sub_heading)
            sheet.write('D7', 'Initial Credit', sub_heading)
            sheet.write('E7', 'Debit', sub_heading)
            sheet.write('F7', 'Credit', sub_heading)
        else:
            sheet.write('C7', 'Debit', sub_heading)
            sheet.write('D7', 'Credit', sub_heading)

        row = 6
        col = 0
        sheet.set_column(5, 0, 15)
        sheet.set_column(6, 1, 15)
        sheet.set_column(7, 2, 26)
        if filters.get('date_from'):
            sheet.set_column(8, 3, 15)
            sheet.set_column(9, 4, 15)
            sheet.set_column(10, 5, 15)
            sheet.set_column(11, 6, 15)
        else:

            sheet.set_column(8, 3, 15)
            sheet.set_column(9, 4, 15)
        for rec_data in report_data_main:

            row += 1
            sheet.write(row, col, rec_data['code'], txt)
            sheet.write(row, col + 1, rec_data['name'], txt)
            if filters.get('date_from'):
                if rec_data.get('Init_balance'):
                    sheet.write(row, col + 2, rec_data['Init_balance']['debit'], txt)
                    sheet.write(row, col + 3, rec_data['Init_balance']['credit'], txt)
                else:
                    sheet.write(row, col + 2, 0, txt)
                    sheet.write(row, col + 3, 0, txt)

                sheet.write(row, col + 4, rec_data['debit'], txt)
                sheet.write(row, col + 5, rec_data['credit'], txt)

            else:
                sheet.write(row, col + 2, rec_data['debit'], txt)
                sheet.write(row, col + 3, rec_data['credit'], txt)
        sheet.write(row+1, col, 'Total', sub_heading)
        if filters.get('date_from'):
            sheet.write(row + 1, col + 4, total.get('debit_total'), txt_l)
            sheet.write(row + 1, col + 5, total.get('credit_total'), txt_l)
        else:
            sheet.write(row + 1, col + 2, total.get('debit_total'), txt_l)
            sheet.write(row + 1, col + 3, total.get('credit_total'), txt_l)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
