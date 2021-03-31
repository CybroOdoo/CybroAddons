from odoo import models, fields, api
import io
import json
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
FETCH_RANGE = 2000


class BankBook(models.TransientModel):
    _name = "dynamic.bank.book"

    journal_ids = fields.Many2many(
        "account.journal",
        string="Journals",
    )
    account_ids = fields.Many2many(
        "account.account",
        string="Accounts",
    )
    account_tag_ids = fields.Many2many("account.account.tag", string="Account Tags")
    analytic_ids = fields.Many2many(
        "account.analytic.account", string="Analytic Accounts"
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
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
    include_details = fields.Boolean(string="Include Details", default=True)

    entries = fields.Selection([('posted', 'All Posted Entries'),
                                ('all', 'All Entries')], string='Target Moves', default='all')

    def report_data(self, title):
        cr = self.env.cr

        data = self.get_filters(default_filters={})
        WHERE = '(1=1)'
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        if data.get('account_tag_ids', []):
            company_domain.append(('tag_ids','in', data.get('account_tag_ids', [])))
        if data.get('account_ids', []):
            company_domain.append(('id','in', data.get('account_ids', [])))
        account_ids = self.env['account.account'].search(company_domain)

        if title == "Bank Book":
            journals = self.env['account.journal'].search([('type', '=', 'bank')],
                                                      limit=1)
        if title == "Cash Book":
            journals = self.env['account.journal'].search([('type', '=', 'cash')],
                                                          limit=1)
        journals_type = journals.id
        WHERE += 'AND j.id = %s' % str(journals_type)

        if data.get('analytic_ids'):
            WHERE += ' AND anl.id IN %s' % str(tuple(data.get('analytic_ids')) + tuple([0]))

        if data.get('entries') == 'posted':
            WHERE += " AND m.state = 'posted'"

        if data.get('analytic_tag_ids'):
            WHERE += ' AND analtag.account_analytic_tag_id IN %s' % str(
                tuple(data.get('analytic_tag_ids')) + tuple([0]))

        move_lines = {
            x.code: {
                'name': x.name,
                'code': x.code,
                'id': x.id,
                'lines': []
            } for x in sorted(account_ids, key=lambda a: a.code)
        }
        for account in account_ids:
            company_id = self.env.user.company_id
            currency = account.company_id.currency_id or company_id.currency_id
            symbol = currency.symbol
            rounding = currency.rounding
            position = currency.position

            opening_balance = 0
            if data.get('date_from') and data.get('date_to'):
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get(
                    'date_to')
                WHERE_CURRENT += " AND a.id = %s" % account.id
            elif data.get('date_from'):
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                    'date_from')
                WHERE_CURRENT += " AND a.id = %s" % account.id
            elif data.get('date_to'):
                WHERE_CURRENT = WHERE + " AND l.date <= '%s'" % data.get(
                    'date_to')
                WHERE_CURRENT += " AND a.id = %s" % account.id
            else:
                WHERE_CURRENT = WHERE + " AND a.id = %s" % account.id
            ORDER_BY_CURRENT = 'l.date'
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
                --GROUP BY l.id, l.account_id,  j.code, l.currency_id, l.date,l.debit_currency, l.credit_currency, l.ref, l.name, m.id, m.name, c.rounding, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                ORDER BY %s
            ''') % (WHERE_CURRENT, ORDER_BY_CURRENT)
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
    def get_filters(self, default_filters={}):
        company_id = self.env.user.company_id
        company_domain = [('company_id','=', company_id.id)]
        journals = self.journal_ids if self.journal_ids else self.env['account.journal'].search(company_domain)
        accounts = self.account_ids if self.account_ids else self.env['account.account'].search(company_domain)
        account_tags = self.account_tag_ids if self.account_tag_ids else self.env['account.account.tag'].search([])
        analytics = self.analytic_ids if self.analytic_ids else self.env['account.analytic.account'].search(
            company_domain)
        analytic_tags = self.analytic_tag_ids if self.analytic_tag_ids else self.env[
            'account.analytic.tag'].sudo().search(
            ['|', ('company_id', '=', company_id.id), ('company_id', '=', False)])
        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'account_ids': self.account_ids.ids,
            'account_tag_ids': self.account_tag_ids.ids,
            'analytic_ids': self.analytic_ids.ids,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'entries': self.entries,
            'journals_list': [(j.id, j.name) for j in journals],
            'accounts_list': [(a.id, a.name) for a in accounts],
            'account_tag_list': [(a.id, a.name) for a in account_tags],
            'analytics_list': [(anl.id, anl.name) for anl in analytics],
            'analytic_tag_list': [(anltag.id, anltag.name) for anltag in analytic_tags],
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

        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All']
        if data.get('include_details'):
            filters['include_details'] = True
        else:
            filters['include_details'] = False

        if data.get('entries'):
            filters['entries'] = data.get('entries')
        if data.get('date_from', False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')
        if data.get('company_id'):
            filters['company_id'] = data.get('company_id')
        else:
            filters['company_id'] = ''
        filters['account_tags'] = ['All']
        filters['analytics'] = ['All']
        filters['analytic_tags'] = ['All']
        filters['journals_list'] = data.get('journals_list')
        filters['accounts_list'] = data.get('accounts_list')
        filters['account_tag_list'] = data.get('account_tag_list')
        filters['analytics_list'] = data.get('analytics_list')
        filters['analytic_tag_list'] = data.get('analytic_tag_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def bb_move_lines(self, offset=0, account=0, fetch_range=FETCH_RANGE):
        cr = self.env.cr
        offset_count = offset * fetch_range
        opening_balance = 0
        data = self.get_filters(default_filters={})

        company_id = self.env.user.company_id

        WHERE = '(1=1)'

        WHERE_CURRENT = WHERE
        WHERE_CURRENT += " AND a.id = %s" % account
        if data.get('entries') == 'posted':
            WHERE += " AND m.state = 'posted'"

        if data.get('date_from') and data.get('date_to'):
            WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                'date_from') + " AND l.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND a.id = %s" % account
        elif data.get('date_from'):
            WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                'date_from')
            WHERE_CURRENT += " AND a.id = %s" % account
        elif data.get('date_to'):
            WHERE_CURRENT = WHERE + " AND l.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND a.id = %s" % account


        else:
            WHERE_CURRENT = WHERE + " AND a.id = %s" % account

        ORDER_BY_CURRENT = 'j.code, p.name, l.move_id, l.date'
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
            GROUP BY j.code, p.name, l.move_id, l.date
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
        ''') % (WHERE_CURRENT)
        cr.execute(sql)
        count = cr.fetchone()[0]

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
                GROUP BY l.id, l.account_id, j.code, l.currency_id, l.amount_currency, l.name, m.id, m.name, c.rounding, cc.id, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                ORDER BY %s
                OFFSET %s ROWS
                FETCH FIRST %s ROWS ONLY
            ''') % (WHERE_CURRENT, ORDER_BY_CURRENT, offset_count, fetch_range)
        cr.execute(sql)
        for row in cr.dictfetchall():
            current_balance = row['balance']
            row['balance'] = opening_balance + current_balance
            opening_balance += current_balance
            row['initial_bal'] = False
            move_lines.append(row)

        return count, offset_count, move_lines


    def get_data(self, title):
        filters = self.process_filters()
        account_lines = self.report_data(title)
        return filters, account_lines


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

        if vals.get('account_tag_ids'):
            vals.update({'account_tag_ids': [(4, j) for j in vals.get('account_tag_ids')]})
        if vals.get('account_tag_ids') == []:
            vals.update({'account_tag_ids': [(5,)]})

        if vals.get('analytic_ids'):
            vals.update({'analytic_ids': [(4, j) for j in vals.get('analytic_ids')]})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})

        if vals.get('analytic_tag_ids'):
            vals.update({'analytic_tag_ids': [(4, j) for j in vals.get('analytic_tag_ids')]})
        if vals.get('analytic_tag_ids') == []:
            vals.update({'analytic_tag_ids': [(5,)]})
        return super(BankBook, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(BankBook, self).create(vals)
        return res

    def get_xlsx_report(self, data, response, report_data, dfr_data):
        i = str(data)
        n = json.loads(i)
        filters = json.loads(report_data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '12px',
             'border': 1,
             'border_color': 'black'})
        sub_heading_sub = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 2,
             'border_color': 'black'})
        sub_heading_total = workbook.add_format(
            {'align': 'right', 'bold': True, 'font_size': '10px',
             'border': 2,
             'border_color': 'black'})
        sub_heading_main = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        sheet.merge_range('A2:J3', self.env.user.company_id.name + ':' + dfr_data, head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})
        if filters.get('date_from'):
            sheet.merge_range('B4:C4', 'From: '+filters.get('date_from') , date_head)
        if filters.get('date_to'):
            sheet.merge_range('H4:I4', 'To: '+ filters.get('date_to'), date_head)
        sheet.merge_range('A5:J6', '  Accounts: ' + ', '.join([ lt or '' for lt in filters['accounts'] ]) +   '  Journals: ' + ', '.join([ lt or '' for lt in filters['journals'] ]) +   '  Account Tags: ' + ', '.join([ lt or '' for lt in filters['account_tags'] ]) +   '  Analytic Tags: ' + ', '.join([ lt or '' for lt in filters['analytic_tags'] ]) +  '  Analytic: ' +', '.join([ at or '' for at in filters['analytics'] ]) + '  Entries: '+ filters.get('entries'), date_head)

        sheet.write('A8', 'Code', sub_heading)
        sheet.write('B8', 'Account', sub_heading)
        sheet.write('C8', 'Date', sub_heading)
        sheet.write('D8', 'JRNL', sub_heading)
        sheet.write('E8', 'Partner', sub_heading)
        sheet.write('F8', 'Move', sub_heading)
        sheet.write('G8', 'Entry Label', sub_heading)
        sheet.write('H8', 'Debit', sub_heading)
        sheet.write('I8', 'Credit', sub_heading)
        sheet.write('J8', 'Balance', sub_heading)
        lst = []
        for rec in n:
            lst.append(rec)
        row = 6
        col = 0
        row_1 = 5
        sheet.set_column(8, 0, 15)
        sheet.set_column('B:B', 40)
        sheet.set_column(8, 2, 15)
        sheet.set_column(8, 3, 15)
        sheet.set_column(8, 4, 15)
        sheet.set_column(8, 5, 15)
        sheet.set_column(8, 6, 50)
        sheet.set_column(8, 7, 26)
        sheet.set_column(8, 8, 15)
        sheet.set_column(8, 9, 15)
        for l in lst:
            one_lst = []
            two_lst = []

            if n[l]['count']:

                one_lst.append(n[l])
                row += 1
                row_1 += 1
                sheet.write(row +1, col, n[l]['code'], sub_heading_sub)
                sheet.write(row +1, col + 1, n[l]['name'], sub_heading_sub)
                sheet.write(row + 1, col + 2, '', sub_heading_sub)
                sheet.write(row + 1, col + 3, '', sub_heading_sub)
                sheet.write(row + 1, col + 4, '', sub_heading_sub)
                sheet.write(row + 1, col + 5, '', sub_heading_sub)
                sheet.write(row + 1, col + 6, '', sub_heading_sub)

                sheet.write(row +1, col + 7, n[l]['debit'], sub_heading_total)
                sheet.write(row +1, col + 8, n[l]['credit'], sub_heading_total)
                sheet.write(row +1, col + 9, n[l]['balance'], sub_heading_total)

                for rec_1 in n[l]['lines']:
                    row_1 += 1
                    row += 1
                    if rec_1['initial_bal']:
                        sheet.write(row +1, col, 'Initial Balance', sub_heading_main)
                        sheet.write(row + 1, col + 1, '', txt)
                        sheet.write(row + 1, col + 2, '', txt)
                        sheet.write(row + 1, col + 3, '', txt)
                        sheet.write(row + 1, col + 4, '', txt)
                        sheet.write(row + 1, col + 5, '', txt)
                        sheet.write(row + 1, col + 6, '', txt)
                        sheet.write(row +1, col + 7, n[l]['debit'], txt)
                        sheet.write(row +1, col + 8, n[l]['credit'], txt)
                        sheet.write(row +1, col + 9, n[l]['balance'], txt)
                    if not rec_1['initial_bal'] and not rec_1['ending_bal']:
                        sheet.write(row + 1, col , '', txt)
                        sheet.write(row + 1, col + 1, '', txt)
                        sheet.write(row +1, col + 2, rec_1.get('ldate'), txt)
                        sheet.write(row +1, col + 3, rec_1.get('lcode'), txt)
                        sheet.write(row +1, col + 4, rec_1.get('partner_name'), txt)
                        sheet.write(row +1, col + 5, rec_1.get('move_name'), txt)
                        sheet.write(row +1, col + 6, rec_1.get('lname'), txt)
                        sheet.write(row +1, col + 7, rec_1.get('debit'), txt)
                        sheet.write(row +1, col + 8, rec_1.get('credit'), txt)
                        sheet.write(row +1, col + 9, rec_1.get('balance'), txt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
