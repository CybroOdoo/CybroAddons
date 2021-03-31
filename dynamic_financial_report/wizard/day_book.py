from datetime import datetime

from odoo import models, fields, api
import io
import json
import datetime
from odoo.http import request
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
FETCH_RANGE = 2500


class DayBook(models.TransientModel):
    _name = "dynamic.day.book"

    journal_ids = fields.Many2many(
        "account.journal",
        string="Journals",
    )
    account_ids = fields.Many2many(
        "account.account",
        string="Accounts",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
    )
    entries = fields.Selection([('posted', 'All Posted Entries'),
                                ('all', 'All Entries')], string='Target Moves',
                               default='all')

    date_from = fields.Date(
        string="Start date",
    )
    date_to = fields.Date(
        string="End date",
    )

    include_details = fields.Boolean(string="Include Details", default=True)

    def report_data(self):
        """ """
        cr = self.env.cr

        data = self.get_filters(default_filters={})

        WHERE = '(1=1)'
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        if data.get('account_ids', []):
            WHERE += ' AND a.id IN %s' % str(
                tuple(data.get('account_ids')) + tuple([0]))

        if data.get('journal_ids'):
            WHERE += ' AND j.id IN %s' % str(
                tuple(data.get('journal_ids')) + tuple([0]))

        if data.get('entries') == 'posted':
            WHERE += " AND m.state = 'posted'"
        day_ids = self.env['account.move.line'].search([])

        move_lines = {
            x.date.strftime('%Y-%m-%d'): {

                'date': x.date,
                'id': x.id,
                'lines': [],
                'days': []
            } for x in day_ids
        }

        for day in day_ids:

            company_id = self.env.user.company_id
            currency = day.company_id.currency_id or company_id.currency_id
            symbol = currency.symbol
            rounding = currency.rounding
            position = currency.position

            opening_balance = 0
            if data.get('date_from') and data.get('date_to'):
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                    'date_from') + " AND l.date <= '%s'" % data.get(
                    'date_to')
                WHERE_CURRENT += " AND l.date = '%s'" % day.date.strftime('%Y-%m-%d')
            elif data.get('date_from'):
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                    'date_from')
                WHERE_CURRENT += " AND l.date = '%s'" % day.date.strftime('%Y-%m-%d')
            elif data.get('date_to'):
                WHERE_CURRENT = WHERE + " AND l.date <= '%s'" % data.get(
                    'date_to')
                WHERE_CURRENT += " AND l.date = '%s'" % day.date.strftime('%Y-%m-%d')
            else:
                WHERE_CURRENT = WHERE + " AND l.date = '%s'" % day.date.strftime('%Y-%m-%d')
            # ORDER_BY_CURRENT = 'l.date'
            sql = ('''
                    SELECT
                     l.date AS ldate,
                     l.account_id AS account_id,
                     l.id AS lid,
                    p.name AS partner_name,
                    m.name AS move_name,
                    l.name AS lname,
                    COALESCE(l.debit,0) AS debit,
                 COALESCE(l.credit,0) AS credit,
                     COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency
                FROM account_move_line l
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN account_move i ON (m.id =i.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                --GROUP BY l.date,l.id,l.currency_id, l.debit_currency, l.credit_currency, l.ref, l.name, m.id, m.name, c.rounding, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                 ORDER BY l.date
            ''') % (WHERE_CURRENT)
            cr.execute(sql)

            current_lines = cr.dictfetchall()

            for row in current_lines:
                current_balance = row['balance']
                row['balance'] = opening_balance + current_balance
                opening_balance += current_balance
                row['initial_bal'] = False

            WHERE_FULL = WHERE + " AND l.date = '%s'" % day.date.strftime('%Y-%m-%d')
            sql = ('''
                SELECT
                    COALESCE(SUM(l.debit),0) AS debit,
                    COALESCE(SUM(l.credit),0) AS credit,
                    COALESCE(SUM(l.debit - l.credit),0) AS balance
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
            ''') % WHERE_FULL
            cr.execute(sql)
            for row in cr.dictfetchall():
                row['ending_bal'] = True
                row['initial_bal'] = False

                move_lines[day.date.strftime('%Y-%m-%d')]['lines'].append(row)

                move_lines[day.date.strftime('%Y-%m-%d')]['debit'] = row['debit']
                move_lines[day.date.strftime('%Y-%m-%d')]['credit'] = row['credit']
                move_lines[day.date.strftime('%Y-%m-%d')]['balance'] = row['balance']
                move_lines[day.date.strftime('%Y-%m-%d')]['company_currency_id'] = currency.id
                move_lines[day.date.strftime('%Y-%m-%d')]['company_currency_symbol'] = symbol
                move_lines[day.date.strftime('%Y-%m-%d')]['company_currency_precision'] = rounding
                move_lines[day.date.strftime('%Y-%m-%d')]['company_currency_position'] = position
                move_lines[day.date.strftime('%Y-%m-%d')]['count'] = len(current_lines)

                move_lines[day.date.strftime('%Y-%m-%d')]['pages'] = self.get_page_list(
                    len(current_lines))
                move_lines[day.date.strftime('%Y-%m-%d')]['single_page'] = True if len(
                    current_lines) <= FETCH_RANGE else False

        return move_lines

    def get_filters(self, default_filters={}):
        """ shows filters """
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        journals = self.journal_ids if self.journal_ids else self.env[
            'account.journal'].search(company_domain)
        accounts = self.account_ids if self.account_ids else self.env[
            'account.account'].search(company_domain)

        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'account_ids': self.account_ids.ids,
            'entries': self.entries,
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'journals_list': [(j.id, j.name) for j in journals],
            'accounts_list': [(a.id, a.name) for a in accounts],

            'company_name': company_id and company_id.name,
        }
        filter_dict.update(default_filters)

        return filter_dict

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})

        filters = {}

        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(
                data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']

        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(
                data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All']

        if data.get('date_from', False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')

        if data.get('entries'):
            filters['entries'] = data.get('entries')
        if data.get('include_details'):
            filters['include_details'] = True
        else:
            filters['include_details'] = False
        filters['company_id'] = ''
        filters['journals_list'] = data.get('journals_list')
        filters['accounts_list'] = data.get('accounts_list')

        filters['company_name'] = data.get('company_name')

        return filters

    def db_move_lines(self, offset=0, account=0, fetch_range=FETCH_RANGE):
        """ shows sub lines ie,details of that particular day book"""
        cr = self.env.cr
        offset_count = offset * fetch_range
        opening_balance = 0
        company_id = self.env.user.company_id
        data = self.get_filters(default_filters={})
        lines = self.report_data()
        dates = []
        for line in lines:
            dates.append(lines.get(line).get('date').strftime("%Y-%m-%d"))

        WHERE = '(1=1)'

        WHERE_CURRENT = WHERE
        WHERE_CURRENT += " AND l.id = %s" % account
        if data.get('entries') == 'posted':
            WHERE += " AND m.state = 'posted'"
        if data.get('account_ids', []):
            WHERE += ' AND a.id IN %s' % str(
                tuple(data.get('account_ids')) + tuple([0]))

        if data.get('journal_ids'):
            WHERE += ' AND j.id IN %s' % str(
                tuple(data.get('journal_ids')) + tuple([0]))
        if data.get('date_from') and data.get('date_to'):
            WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                'date_from') + " AND l.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND l.id = %s" % account
        elif data.get('date_from'):
            WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                'date_from')
            WHERE_CURRENT += " AND l.id = %s" % account
        elif data.get('date_to'):
            WHERE_CURRENT = WHERE + " AND l.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND l.id = %s" % account


        else:
            WHERE_CURRENT = WHERE + " AND l.id = %s" % account

        ORDER_BY_CURRENT = 'j.code,l.date, p.name, l.move_id'
        move_lines = []
        sql = ('''
            SELECT 
                COALESCE(SUM(l.debit - l.credit),0) AS balance
            FROM account_move_line l
            JOIN account_move m ON (l.move_id=m.id)
            JOIN account_account a ON (l.account_id=a.id)
            LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
            LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
            LEFT JOIN res_currency c ON (l.currency_id=c.id)
            LEFT JOIN res_partner p ON (l.partner_id=p.id)
            JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
            GROUP BY j.code,l.date, p.name, l.move_id
            ORDER BY %s
            OFFSET %s ROWS
            FETCH FIRST %s ROWS ONLY
        ''') % (WHERE_CURRENT, ORDER_BY_CURRENT, 0, offset_count)
        cr.execute(sql)
        running_balance_list = cr.fetchall()
        for running_balance in running_balance_list:
            opening_balance += running_balance[0]

        sql = ('''
            SELECT COUNT(*)
            FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
        ''') % (WHERE)
        cr.execute(sql)
        count = cr.fetchone()[0]

        val = WHERE

        for line in lines:
            sql = ('''
                    SELECT

                        l.date AS ldate,
                        l.id AS lid,
                        l.account_id AS account_id,
                        j.code AS lcode,
                        l.currency_id,
                        --l.ref AS lref,
                        l.name AS lname,
                        m.id AS move_id,
                        m.name AS move_name,
                        c.symbol AS currency_symbol,
                        c.position AS currency_position,
                        c.rounding AS currency_precision,
                        cc.id AS company_currency_id,
                        cc.symbol AS company_currency_symbol,
                        cc.rounding AS company_currency_precision,
                        cc.position AS company_currency_position,
                        p.name AS partner_name,
                        COALESCE(l.debit,0) AS debit,
                        COALESCE(l.credit,0) AS credit,
                        COALESCE(l.debit - l.credit,0) AS balance,
                        COALESCE(l.amount_currency,0) AS amount_currency
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                    GROUP BY l.id, l.account_id, j.code,l.date, l.currency_id, l.amount_currency, l.name, m.id, m.name, c.rounding, cc.id, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                    ORDER BY %s
                    OFFSET %s ROWS
                    FETCH FIRST %s ROWS ONLY
                ''') % (val, ORDER_BY_CURRENT, offset_count, fetch_range)
            cr.execute(sql)

        for row in cr.dictfetchall():
            days = lines.get(row.get('ldate').strftime("%Y-%m-%d"))
            if days:
                if days.get('date'):
                    row['parent_id'] = days.get('date').strftime("%Y-%m-%d")

            move_lines.append(row)

        return count, offset_count, move_lines, dates

    def get_data(self):
        """ shows complete data of day book"""
        filters = self.process_filters()
        account_lines = self.report_data()

        db_lines = self.db_move_lines()

        return filters, account_lines, db_lines

    def get_page_list(self, total_count):

        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i + 1 for i in range(0, int(page_count))] or []

    def write(self, vals):

        if vals.get('journal_ids'):
            vals.update(
                {'journal_ids': [(4, j) for j in vals.get('journal_ids')]})

        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})

        if vals.get('account_ids'):
            vals.update(
                {'account_ids': [(4, j) for j in vals.get('account_ids')]})
        if vals.get('account_ids') == []:
            vals.update({'account_ids': [(5,)]})

        return super(DayBook, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(DayBook, self).create(vals)
        return res

    def get_xlsx_report(self, data, response, report_data, dfr_data):
        """ fetch xlsx report"""
        i_data = str(data)
        n_data = json.loads(i_data)
        output = io.BytesIO()
        value = json.loads(report_data)

        filters = json.loads(dfr_data)

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        cell_format = workbook.add_format(
            {'align': 'center', 'bold': True, 'bg_color': '#d3d3d3;',
             'border': 1})

        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})

        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        sub_heading_sub = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 2,
             'border_color': 'black'})
        sheet.merge_range('B2:G3',
                          self.env.user.company_id.name + ':' + ' Day Book',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})

        if filters.get('date_from'):
            sheet.merge_range('A4:C4',
                              'From Date: ' + filters.get('date_from'),
                              date_head)
        if filters.get('date_to'):
            sheet.merge_range('D4:E4', 'To Date: ' + filters.get('date_to'),
                              date_head)

        sheet.merge_range('F4:G4', 'Target Moves: ' + filters.get('entries'),
                          date_head)

        sheet.merge_range('B5:D5', '  Journals: ' + ', '.join(
            [lt or '' for lt in
             filters['journals']]), date_head)
        sheet.merge_range('E5:F5', ' Accounts: ' + ', '.join(
            [lt or '' for lt in
             filters['accounts']]),
                          date_head)
        sheet.merge_range('A6:E6', 'Date', cell_format)
        sheet.write('F6', 'Debit', cell_format)
        sheet.write('G6', 'Credit', cell_format)
        sheet.write('H6', 'Balance', cell_format)

        lst = []
        for rec in n_data:
            lst.append(rec)
        row = 5
        col = 0
        row_1 = 5
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 26)
        sheet.set_column(4, 4, 26)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 26)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)

        for l_rec in lst:
            one_lst = []
            two_lst = []

            if n_data[l_rec]['count']:
                one_lst.append(n_data[l_rec])

                sheet.merge_range(row + 1, col, row + 1, col + 4,
                                  n_data[l_rec]['date'], sub_heading_sub)
                sheet.write(row + 1, col + 5, n_data[l_rec]['debit'], sub_heading_sub)
                sheet.write(row + 1, col + 6, n_data[l_rec]['credit'], sub_heading_sub)
                sheet.write(row + 1, col + 7, n_data[l_rec]['balance'], sub_heading_sub)

                #
                row += 2
                sheet.write(row, col, 'Date', cell_format)
                sheet.write(row, col + 1, 'JRNL', cell_format)
                sheet.write(row, col + 2, 'Partner', cell_format)
                sheet.write(row, col + 3, 'Move', cell_format)
                sheet.write(row, col + 4, 'Entry Label', cell_format)
                sheet.write(row, col + 5, 'Debit', cell_format)
                sheet.write(row, col + 6, 'Credit', cell_format)
                sheet.write(row, col + 7, 'balance', cell_format)

                for r_rec in value:
                    if n_data[l_rec]['date'] == r_rec['ldate']:
                        row += 1
                        sheet.write(row, col, r_rec['ldate'], txt)
                        sheet.write(row, col + 1, r_rec['lcode'], txt)
                        sheet.write(row, col + 2, r_rec['partner_name'], txt)
                        sheet.write(row, col + 3, r_rec['lname'], txt)
                        sheet.write(row, col + 4, r_rec['move_name'], txt)
                        sheet.write(row, col + 5, r_rec['debit'], txt)
                        sheet.write(row, col + 6, r_rec['credit'], txt)
                        sheet.write(row, col + 7, r_rec['balance'], txt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()