from odoo import models, fields, api
import io
import json
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
FETCH_RANGE = 2000


class BalanceSheetModel(models.TransientModel):
    _name = "dynamic.balance.sheet"

    journal_ids = fields.Many2many(
        "account.journal",
        string="Journals",
    )
    account_ids = fields.Many2many(
        "account.account",
        string="Accounts",
    )
    account_tag_ids = fields.Many2many("account.account.tag",
                                       string="Account Tags")
    analytic_ids = fields.Many2many(
        "account.analytic.account", string="Analytic Accounts"
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag",
                                        string="Analytic Tags")
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
                                ('all', 'All Entries')], string='Target Moves',
                               default='all')

    def report_data(self, tag):
        cr = self.env.cr

        data = self.get_filters(default_filters={})
        WHERE = '(1=1)'
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        if data.get('account_tag_ids', []):
            company_domain.append(
                ('tag_ids', 'in', data.get('account_tag_ids', [])))
        if data.get('account_ids', []):
            company_domain.append(('id', 'in', data.get('account_ids', [])))
        account_ids = self.env['account.account'].search(company_domain)

        if data.get('journal_ids'):
            WHERE += ' AND j.id IN %s' % str(
                tuple(data.get('journal_ids')) + tuple([0]))

        if data.get('analytic_ids'):
            WHERE += ' AND anl.id IN %s' % str(
                tuple(data.get('analytic_ids')) + tuple([0]))

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
                'lines': [],
                'type': x.user_type_id.internal_group,
                'type_id': x.user_type_id
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
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                    'date_from') + " AND l.date <= '%s'" % data.get(
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
                move_lines[account.code][
                    'company_currency_precision'] = rounding
                move_lines[account.code]['company_currency_position'] = position
                move_lines[account.code]['count'] = len(current_lines)
                move_lines[account.code]['pages'] = self.get_page_list(
                    len(current_lines))
                move_lines[account.code]['single_page'] = True if len(
                    current_lines) <= FETCH_RANGE else False
        if tag == 'Balance Sheet Report':
            account_report_id = self.env['account.financial.report'].search([
                ('name', 'ilike', 'Balance Sheet')])
        if tag == 'Profit and Loss Report':
            account_report_id = self.env['account.financial.report'].search([
                ('name', 'ilike', 'Profit and Loss')])

        new_data = {'id': self.id, 'date_from': self.date_from,
                    'enable_filter': True,
                    'debit_credit': True, 'date_to': self.date_to,
                    'account_report_id': account_report_id,
                    'target_move': self.entries,
                    'view_format': 'vertical',
                    'company_id': self.company_id,
                    'used_context': {'journal_ids': False,
                                     'state': self.entries,
                                     'date_from': self.date_from,
                                     'date_to': self.date_to,
                                     'strict_range': False,
                                     'company_id': self.company_id,
                                     'lang': 'en_US'}}

        account_lines = self.get_account_lines(new_data)

        report_lines = self.view_report_pdf(account_lines, new_data)[
            'report_lines']

        move_line_accounts = []
        move_line_counts = []

        for rec in move_lines:

            if move_lines[rec]['count'] != 0:
                move_line_accounts.append(move_lines[rec]['code'])
            move_line_counts.append(move_lines[rec]['count'])

        report_lines_move = []
        parent_list = []

        def filter_movelines_parents(obj):
            for each in obj:
                if each['report_type'] == 'accounts':
                    if each['code'] in move_line_accounts:
                        report_lines_move.append(each)
                        parent_list.append(each['p_id'])
                elif each['report_type'] == 'account_report':
                    report_lines_move.append(each)
                else:
                    report_lines_move.append(each)

        filter_movelines_parents(report_lines)

        parent_list = list(set(parent_list))

        max_level = 0
        for rep in report_lines_move:
            if rep['level'] > max_level:
                max_level = rep['level']

        def get_parents(obj):
            for item in report_lines_move:
                for each in obj:
                    if item['report_type'] != 'account_type' and each in item['c_ids']:
                        obj.append(item['r_id'])

                if item['report_type'] == 'account_report':
                    obj.append(item['r_id'])
                    break

        get_parents(parent_list)

        for i in range(max_level):
            get_parents(parent_list)

        parent_list = list(set(parent_list))

        final_report_lines = []

        for rec in report_lines_move:
            if rec['report_type'] != 'accounts':
                if rec['r_id'] in parent_list:
                    final_report_lines.append(rec)
            else:
                final_report_lines.append(rec)

        def filter_sum(obj):
            sum_list = {}
            for pl in parent_list:
                sum_list[pl] = {}
                sum_list[pl]['s_debit'] = 0
                sum_list[pl]['s_credit'] = 0
                sum_list[pl]['s_balance'] = 0

            for each in obj:
                if each['p_id'] and each['p_id'] in parent_list:
                    sum_list[each['p_id']]['s_debit'] += each['debit']
                    sum_list[each['p_id']]['s_credit'] += each['credit']
                    sum_list[each['p_id']]['s_balance'] += each['balance']
            return sum_list

        def assign_sum(obj):
            for each in obj:
                if each['r_id'] in parent_list and each['report_type'] != 'account_report':
                    each['debit'] = sum_list_new[each['r_id']]['s_debit']
                    each['credit'] = sum_list_new[each['r_id']]['s_credit']

        for p in range(max_level):
            sum_list_new = filter_sum(final_report_lines)
            assign_sum(final_report_lines)

        company_id = self.env.user.company_id
        currency = company_id.currency_id
        symbol = currency.symbol
        rounding = currency.rounding
        position = currency.position

        for rec in final_report_lines:
            rec['debit'] = round(rec['debit'], 2)
            rec['credit'] = round(rec['credit'], 2)
            rec['balance'] = rec['debit'] - rec['credit']
            rec['balance'] = round(rec['balance'], 2)
            if position == "before":
                rec['m_debit'] = symbol + " " + str(rec['debit'])
                rec['m_credit'] = symbol + " " + str(rec['credit'])
                rec['m_balance'] = symbol + " " + str(rec['balance'])

            else:
                rec['m_debit'] = str(rec['debit']) + " " + symbol
                rec['m_credit'] = str(rec['credit']) + " " + symbol
                rec['m_balance'] = str(rec['balance']) + " " + symbol

        return move_lines, final_report_lines


    def get_filters(self, default_filters={}):
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        journals = self.journal_ids if self.journal_ids else self.env[
            'account.journal'].search(company_domain)
        accounts = self.account_ids if self.account_ids else self.env[
            'account.account'].search(company_domain)
        account_tags = self.account_tag_ids if self.account_tag_ids else \
            self.env['account.account.tag'].search([])
        analytics = self.analytic_ids if self.analytic_ids else self.env[
            'account.analytic.account'].search(
            company_domain)
        analytic_tags = self.analytic_tag_ids if self.analytic_tag_ids else \
            self.env[
                'account.analytic.tag'].sudo().search(
                ['|', ('company_id', '=', company_id.id),
                 ('company_id', '=', False)])
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
            'analytic_tag_list': [(anltag.id, anltag.name) for anltag in
                                  analytic_tags],
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

    def bs_move_lines(self, offset=0, account=0, fetch_range=FETCH_RANGE):
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

    def get_data(self, tag):
        filters = self.process_filters()
        account_lines = self.report_data(tag)[0]
        report_lines = self.report_data(tag)[1]

        return filters, account_lines, report_lines

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

        if vals.get('account_tag_ids'):
            vals.update({'account_tag_ids': [(4, j) for j in
                                             vals.get('account_tag_ids')]})
        if vals.get('account_tag_ids') == []:
            vals.update({'account_tag_ids': [(5,)]})

        if vals.get('analytic_ids'):
            vals.update(
                {'analytic_ids': [(4, j) for j in vals.get('analytic_ids')]})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})

        if vals.get('analytic_tag_ids'):
            vals.update({'analytic_tag_ids': [(4, j) for j in
                                              vals.get('analytic_tag_ids')]})
        if vals.get('analytic_tag_ids') == []:
            vals.update({'analytic_tag_ids': [(5,)]})

        return super(BalanceSheetModel, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(BalanceSheetModel, self).create(vals)
        return res

    def get_xlsx_report(self, data, response, report_data, dfr_data):

        i_data = str(data)
        filters = json.loads(report_data)
        j_data = dfr_data
        rl_data = json.loads(j_data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        side_heading_main = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})

        side_heading_sub = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})

        side_heading_sub.set_indent(1)
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_name = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_name_bold = workbook.add_format({'font_size': '10px', 'border': 1,
                                             'bold': True})
        txt_name.set_indent(2)
        txt_name_bold.set_indent(2)

        txt = workbook.add_format({'font_size': '10px', 'border': 1})

        sheet.merge_range('A2:D3',
                          self.env.user.company_id.name + ' : ' + i_data,
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})

        date_head_left = workbook.add_format({'align': 'left', 'bold': True,
                                              'font_size': '10px'})

        date_head_right = workbook.add_format({'align': 'right', 'bold': True,
                                               'font_size': '10px'})

        date_head_left.set_indent(1)
        date_head_right.set_indent(1)

        if filters.get('date_from'):
            sheet.merge_range('A4:B4', 'From: ' + filters.get('date_from'),
                              date_head_left)
        if filters.get('date_to'):
            sheet.merge_range('C4:D4', 'To: ' + filters.get('date_to'),
                              date_head_right)
        sheet.merge_range('A5:D6', '  Accounts: ' + ', '.join(
            [lt or '' for lt in
             filters['accounts']]) + '  Journals: ' + ', '.join(
            [lt or '' for lt in
             filters['journals']]) + '  Account Tags: ' + ', '.join(
            [lt or '' for lt in
             filters['account_tags']]) + '  Analytic Tags: ' + ', '.join(
            [lt or '' for lt in
             filters['analytic_tags']]) + '  Analytic: ' + ', '.join(
            [at or '' for at in
             filters['analytics']]) + '  Entries: ' + filters.get(
            'entries'), date_head)

        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)

        row = 5
        col = 0

        row += 2
        sheet.write(row, col, '', sub_heading)
        sheet.write(row, col + 1, 'Debit', sub_heading)
        sheet.write(row, col + 2, 'Credit', sub_heading)
        sheet.write(row, col + 3, 'Balance', sub_heading)

        if rl_data:
            for fr in rl_data:

                row += 1
                if fr['level'] == 1:
                    sheet.write(row, col, fr['name'], side_heading_main)
                elif fr['level'] == 2:
                    sheet.write(row, col, fr['name'], side_heading_sub)
                else:
                    sheet.write(row, col, fr['name'], txt_name)
                sheet.write(row, col + 1, fr['debit'], txt)
                sheet.write(row, col + 2, fr['credit'], txt)
                sheet.write(row, col + 3, fr['balance'], txt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
