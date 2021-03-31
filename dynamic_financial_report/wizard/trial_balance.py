from odoo import models, fields, api
import io
import json
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
FETCH_RANGE = 2000


class TrialBalance(models.TransientModel):
    _name = "dynamic.trial.balance"

    journal_ids = fields.Many2many(
        "account.journal",
        string="Journals",
    )
    account_ids = fields.Many2many(
        "account.account",
        string="Accounts",
    )
    analytic_ids = fields.Many2many(
        "account.analytic.account", string="Analytic Accounts"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
    )
    date_from = fields.Date(
        string="Start date",
    )
    date_to = fields.Date(
        string="End date",
    )
    entries = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')], string='Target Moves', default='all')
    include_details = fields.Boolean(string="Include Details", default=True)

    def report_data(self):
        cr = self.env.cr
        data = self.get_filters(default_filters={})
        WHERE = '(1=1)'
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        account_ids = self.env['account.account'].search(company_domain)
        if data.get('journal_ids'):
            WHERE += ' AND j.id IN %s' % str(tuple(data.get('journal_ids')) + tuple([0]))
        if data.get('entries') == 'posted':
            WHERE += " AND m.state = 'posted'"


        if data.get('analytic_ids'):
            WHERE += ' AND anl.id IN %s' % str(tuple(data.get('analytic_ids')) + tuple([0]))
        move_lines = {
            x.code: {
                'name': x.name,
                'code': x.code,
                'id': x.id,
                'lines': [],

            } for x in sorted(account_ids, key=lambda a: a.code)

        }
        for account in account_ids:
            company_id = self.env.user.company_id
            currency = account.company_id.currency_id or company_id.currency_id
            symbol = currency.symbol
            rounding = currency.rounding
            position = currency.position

            opening_balance = 0

            WHERE_INIT = WHERE + " AND l.date < '%s'" % data.get('date_from')
            WHERE_INIT += " AND l.account_id = %s" % account.id
            if data.get('date_from'):
                sql_b = ('''
                                SELECT 
                                    COALESCE(SUM(l.debit),0) AS debit, 
                                    COALESCE(SUM(l.credit),0) AS credit, 
                                    COALESCE(SUM(l.debit - l.credit),0) AS balance
                                FROM account_move_line l
                                JOIN account_move m ON (l.move_id=m.id)
                                JOIN account_account a ON (l.account_id=a.id)
                                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                                JOIN account_journal j ON (l.journal_id=j.id)
                                WHERE %s
                            ''') % WHERE_INIT
                cr.execute(sql_b)
                bal = cr.dictfetchall()
                for row in bal:
                    row['move_name'] = 'Initial Balance'
                    row['account_id'] = account.id
                    row['initial_bal'] = True
                    row['ending_bal'] = False
                    opening_balance += row['balance']
                    move_lines[account.code]['lines'].append(row)

            if data.get('date_from') and data.get('date_to'):
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
                    'date_to')
                WHERE_CURRENT += " AND a.id = %s" % account.id
            else:
                WHERE_CURRENT = WHERE + " AND a.id = %s" % account.id
            sql = ('''
                    SELECT
                     l.date AS ldate,
                     l.id AS lid,
                    j.code AS lcode,
                 p.name AS partner_name,
                    m.name AS move_name,
                    l.name AS lname,
                    COALESCE(l.debit,0) AS debit,
                 COALESCE(l.credit,0) AS credit,
                     COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency
                FROM account_move_line l
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON (analtag.account_move_line_id=l.id)
                LEFT JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN account_move i ON (m.id =i.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                --GROUP BY l.id, l.account_id,  j.code, l.currency_id, l.debit_currency, l.credit_currency, l.ref, l.name, m.id, m.name, c.rounding, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
            ''') % (WHERE_CURRENT)

            cr.execute(sql)
            current_lines = cr.dictfetchall()
            for row in current_lines:
                row['initial_bal'] = False
                row['ending_bal'] = False

                current_balance = row['balance']
                row['balance'] = opening_balance + current_balance
                opening_balance += current_balance
                row['initial_bal'] = False

                move_lines[account.code]['lines'].append(row)
            WHERE_FULL = WHERE + " AND a.id = %s" % account.id
            sql = ('''
                SELECT
                    COALESCE(SUM(l.debit),0) AS debit,
                    COALESCE(SUM(l.credit),0) AS credit,
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
            ''') % WHERE_FULL
            cr.execute(sql)

            for row in cr.dictfetchall():
                row['ending_bal'] = True
                row['initial_bal'] = False
                move_lines[account.code]['lines'].append(row)
                move_lines[account.code]['debit'] = row['debit']
                move_lines[account.code]['credit'] = row['credit']
                move_lines[account.code]['balance'] = row['balance']
                move_lines[account.code]['company_currency_id'] = currency.id
                move_lines[account.code]['company_currency_symbol'] = symbol
                move_lines[account.code]['company_currency_precision'] = rounding
                move_lines[account.code]['company_currency_position'] = position
                move_lines[account.code]['count'] = len(current_lines)
                move_lines[account.code]['pages'] = self.get_page_list(len(current_lines))
                move_lines[account.code]['single_page'] = True if len(current_lines) <= FETCH_RANGE else False

        return move_lines

    def get_credit_debit_total(self):
        move_line = self.report_data()
        l_keys = move_line.keys()
        debit = 0
        credit = 0
        currency_details = []
        for rec in l_keys:
            single_line = move_line[rec]
            if single_line['count']:
                debit += single_line['debit']
                credit += single_line['credit']
                c_detail = {
                    'currency': single_line['company_currency_id'],
                    'symbol':single_line['company_currency_symbol'],
                    'rounding':single_line['company_currency_precision'],
                    'position':single_line['company_currency_position'],

                }
                if c_detail not in currency_details:
                    currency_details.append(c_detail)
        total = {
            'debit': debit,
            'credit':credit,
            'currency_details':currency_details
        }
        return total


    @api.model
    def get_filters(self, default_filters={}):
        company_id = self.env.user.company_id
        company_domain = [('company_id','=', company_id.id)]
        journals = self.journal_ids if self.journal_ids else self.env['account.journal'].search(company_domain)
        accounts = self.account_ids if self.account_ids else self.env['account.account'].search(company_domain)
        analytics = self.analytic_ids if self.analytic_ids else self.env['account.analytic.account'].search(
            company_domain)

        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'analytic_ids': self.analytic_ids.ids,
            'company_id': company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'entries':self.entries,
            'journals_list': [(j.id, j.name) for j in journals],
            'accounts_list': [(a.id, a.name) for a in accounts],
            'analytics_list': [(anl.id, anl.name) for anl in analytics],
            'company_name': company_id and company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def process_filters(self):
        ''' To show on report headers'''
        data = self.get_filters(default_filters={})
        filters = {}
        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('entries'):
            filters['entries'] = data.get('entries')
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')

        filters['analytics'] = ['All']
        filters['company_id'] = ''
        filters['journals_list'] = data.get('journals_list')
        filters['analytics_list'] = data.get('analytics_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def get_data(self):
        filters = self.process_filters()
        account_lines = self.report_data()
        total = self.get_credit_debit_total()
        return filters, account_lines, total


    def get_page_list(self, total_count):
        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i + 1 for i in range(0, int(page_count))] or []

    def write(self, vals):
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(4, j) for j in vals.get('journal_ids')]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})
        if vals.get('account_ids'):
            vals.update({'account_ids': [(4, j) for j in vals.get('account_ids')]})
        if vals.get('account_ids') == []:
            vals.update({'account_ids': [(5,)]})
        if vals.get('analytic_ids'):
            vals.update({'analytic_ids': [(4, j) for j in vals.get('analytic_ids')]})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})
        return super(TrialBalance, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(TrialBalance, self).create(vals)
        return res


    def get_xlsx_report(self, data, response ,report_data, dfr_data):

        i_data = str(data)
        acount_line = json.loads(i_data)
        total_sub = json.loads(report_data)
        output = io.BytesIO()
        total = json.loads(total_sub['d1'])
        filters = json.loads(total_sub['d2'])
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
        sheet.merge_range('A5:D6', 'Journals: ' + ', '.join([ lt or '' for lt in filters['journals'] ]) + '  Analytic: ' +', '.join([ at or '' for at in filters['analytics'] ]) + '  Entries: '+ filters.get('entries'), date_head)
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
        lst = []
        for rec in acount_line:
            lst.append(rec)
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
        for l in lst:
            one_lst = []
            two_lst = []

            if acount_line[l]['count']:
                one_lst.append(acount_line[l])

                row += 1
                sheet.write(row, col, acount_line[l]['code'], txt)
                sheet.write(row, col + 1, acount_line[l]['name'], txt)
                if filters.get('date_from'):
                    for i_b in acount_line[l]['lines']:
                        if i_b['initial_bal']:
                            sheet.write(row, col + 2, i_b['debit'], txt)
                            sheet.write(row, col + 3, i_b['credit'], txt)
                    sheet.write(row, col + 4, acount_line[l]['debit'], txt)
                    sheet.write(row, col + 5, acount_line[l]['credit'], txt)

                else:
                    sheet.write(row, col + 2, acount_line[l]['debit'], txt)
                    sheet.write(row, col + 3, acount_line[l]['credit'], txt)
        sheet.write(row+1, col, 'Total', sub_heading)
        if filters.get('date_from'):
            sheet.write(row + 1, col + 4, total['debit'], txt_l)
            sheet.write(row + 1, col + 5, total['credit'], txt_l)
        else:
            sheet.write(row + 1, col + 2, total['debit'], txt_l)
            sheet.write(row + 1, col + 3, total['credit'], txt_l)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
