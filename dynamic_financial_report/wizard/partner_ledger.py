import io
import json
from odoo import models, fields, api

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
FETCH_RANGE = 2000


class PartnerLedger(models.TransientModel):
    _name = "dynamic.partner.ledger"
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
    date_from = fields.Date(
        string="Start date",
    )
    date_to = fields.Date(
        string="End date",
    )
    partner_ids = fields.Many2many('res.partner', string='Partner')
    partner_category_ids = fields.Many2many('res.partner.category',
                                            string='Partner_tags')
    include_details = fields.Boolean(string="Include Details", default=True)
    reconciled = fields.Selection([
        ('unreconciled', 'Unreconciled Only')],
        string='Reconcile Type')
    type = fields.Selection(
        [('receivable', 'Receivable Only'),
         ('payable', 'Payable only')],
        string='Account Type', required=False
    )
    target_moves = fields.Selection(
        [('all_entries', 'All entries'),
         ('posted_only', 'Posted Only')], string='Target Moves',
        default='all_entries'
    )

    def process_filters(self):
        # To show on report headers

        data = self.get_filters(default_filters={})
        filters = {}
        if data.get('partner_ids', []):
            filters['partners'] = self.env['res.partner'].browse(
                data.get('partner_ids', [])).mapped('name')
        else:
            filters['partners'] = ['All']

        if data.get('journal_ids', []):
            filters['journals'] = self.env['account.journal'].browse(
                data.get('journal_ids', [])).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(
                data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All Payable and Receivable']

        if data.get('partner_category_ids', []):
            filters['categories'] = self.env['res.partner.category'].browse(
                data.get('partner_category_ids', [])).mapped('name')
        else:
            filters['categories'] = ['All']

        if data.get('date_from', False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')

        if data.get('reconciled') == 'unreconciled':
            filters['reconciled'] = 'Uneconciled'

        if data.get('target_moves') == 'all_entries':
            filters['target_moves'] = 'All Entries'
        else:
            filters['target_moves'] = 'Posted Only'

        if data.get('type') == 'receivable':
            filters['type'] = 'Receivable'
        elif data.get('type') == 'payable':
            filters['type'] = 'Payable'
        else:
            filters['type'] = 'Receivable and Payable'

        if data.get('company_id'):
            filters['company_id'] = data.get('company_id')
        else:
            filters['company_id'] = ''

        if data.get('include_details'):
            filters['include_details'] = True
        else:
            filters['include_details'] = False

        filters['journals_list'] = data.get('journals_list')
        filters['accounts_list'] = data.get('accounts_list')
        filters['partners_list'] = data.get('partners_list')
        filters['category_list'] = data.get('category_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def get_filters(self, default_filters={}):
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        account_domain = [('company_id', '=', company_id.id), (
            'user_type_id.type', 'in', ('receivable', 'payable'))]
        partner_company_domain = [('parent_id', '=', False),
                                  '|',
                                  ('company_id', '=', company_id.id),
                                  ('company_id', '=', False)]

        journals = self.journal_ids if self.journal_ids else self.env[
            'account.journal'].search(company_domain)
        accounts = self.account_ids if self.account_ids else self.env[
            'account.account'].search(account_domain)
        partners = self.partner_ids if self.partner_ids else self.env[
            'res.partner'].search(partner_company_domain)
        categories = self.partner_category_ids if self.partner_category_ids else \
            self.env['res.partner.category'].search([])

        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'account_ids': self.account_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'partner_category_ids': self.partner_category_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'reconciled': self.reconciled,
            'type': self.type,
            'target_moves': self.target_moves,
            'journals_list': [(j.id, j.name) for j in journals],
            'accounts_list': [(a.id, a.name) for a in accounts],
            'partners_list': [(p.id, p.name) for p in partners],
            'category_list': [(c.id, c.name) for c in categories],
            'company_name': self.company_id and self.company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def get_data(self):
        filters = self.process_filters()
        account_lines = self.report_data()
        return filters, account_lines

    def get_page_list(self, total_count):
        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i + 1 for i in range(0, int(page_count))] or []

    @api.model
    def create(self, vals):
        ret = super(PartnerLedger, self).create(vals)
        return ret

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
        if vals.get('partner_ids'):
            vals.update(
                {'partner_ids': [(4, j) for j in vals.get('partner_ids')]})
        if vals.get('partner_ids') == []:
            vals.update({'partner_ids': [(5,)]})

        if vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(4, j) for j in vals.get(
                'partner_category_ids')]})
        if vals.get('partner_category_ids') == []:
            vals.update({'partner_category_ids': [(5,)]})

        ret = super(PartnerLedger, self).write(vals)
        return ret

    def report_data(self):
        # Summary details of each partner
        cr = self.env.cr
        data = self.get_filters(default_filters={})
        WHERE = '1=1'
        company_id = self.env.user.company_id
        partner_company_domain = [('parent_id', '=', False),
                                  '|',
                                  ('company_id', '=', company_id.id),
                                  ('company_id', '=', False)]
        if self.partner_category_ids:
            partner_company_domain.append(
                ('category_id', 'in', self.partner_category_ids.ids))

        if data.get('partner_ids', []):
            partner_ids = self.env['res.partner'].browse(
                data.get('partner_ids'))
        else:
            partner_ids = self.env['res.partner'].search(partner_company_domain)

        move_lines = {
            x.id: {
                'name': x.name,
                'code': x.id,
                'id': x.id,
                'lines': []
            } for x in partner_ids
        }
        for partner in partner_ids:
            company_id = self.env.user.company_id
            currency = partner.company_id.currency_id or company_id.currency_id
            symbol = currency.symbol
            rounding = currency.rounding
            position = currency.position

            opening_balance = 0.0
            type = ('receivable', 'payable')
            if self.type:
                type = tuple([self.type, 'none'])
                WHERE += ' AND ty.type IN %s' % str(type)

            if data.get('reconciled') == 'unreconciled':
                WHERE += ' AND l.amount_residual != 0'

            if data.get('journal_ids', []):
                WHERE += ' AND j.id IN %s' % str(
                    tuple(data.get('journal_ids')) + tuple([0]))

            if data.get('account_ids', []):
                WHERE += ' AND a.id IN %s' % str(
                    tuple(data.get('account_ids')) + tuple([0]))

            if data.get('partner_ids', []):
                WHERE += ' AND p.id IN %s' % str(
                    tuple(data.get('partner_ids')) + tuple([0]))

            if data.get('company_id', False):
                WHERE += ' AND l.company_id = %s' % data.get('company_id')

            if data.get('target_moves') == 'posted_only':
                WHERE += " AND m.state = 'posted'"

            if data.get('date_from') and data.get('date_to'):
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                    'date_from') + " AND l.date <= '%s'" % data.get(
                    'date_to')
                WHERE_CURRENT += " AND p.id = %s" % partner.id
            elif data.get('date_from'):
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                    'date_from')
                WHERE_CURRENT += " AND p.id = %s" % partner.id
            elif data.get('date_to'):
                WHERE_CURRENT = WHERE + " AND l.date <= '%s'" % data.get(
                    'date_to')
                WHERE_CURRENT += " AND p.id = %s" % partner.id
            else:
                WHERE_CURRENT = WHERE + " AND p.id = %s" % partner.id

            ORDER_BY_CURRENT = 'l.date'

            sql = ('''
                SELECT
                    l.date AS ldate,
                    l.id AS lid,
                    j.code AS lcode,
                    a.name AS account_name,
                    a.code AS account_code,
                    m.name AS move_name,
                    l.name AS lname,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.balance,0) AS balance,
                    COALESCE(l.amount_currency,0) AS balance_currency
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id) 
                LEFT JOIN account_account_type AS ty ON (a.user_type_id = ty.id )
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                AND ty.type IN %s
                --GROUP BY l.id, l.account_id, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.id, m.name, c.rounding, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                ORDER BY %s
            ''') % (WHERE_CURRENT, type, ORDER_BY_CURRENT)
            cr.execute(sql)
            current_lines = cr.dictfetchall()
            for row in current_lines:
                row['initial_bal'] = False
                row['ending_bal'] = False

                current_balance = row['balance']
                row['balance'] = opening_balance + current_balance
                opening_balance += current_balance
                row['initial_bal'] = False

                move_lines[partner.id]['lines'].append(row)
            WHERE_FULL = WHERE + " AND p.id = %s" % partner.id
            sql = ('''
                SELECT 
                    COALESCE(SUM(l.debit),0) AS debit, 
                    COALESCE(SUM(l.credit),0) AS credit, 
                    COALESCE(SUM(l.debit - l.credit),0) AS balance
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON (a.user_type_id = ty.id )
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                AND ty.type IN %s
            ''') % (WHERE_FULL, type)
            cr.execute(sql)
            for row in cr.dictfetchall():
                if (data.get(
                        'display_accounts') == 'balance_not_zero' and currency.is_zero(
                    row['debit'] - row['credit'])) \
                        or (data.get('balance_less_than_zero') and (
                        row['debit'] - row['credit']) > 0) \
                        or (data.get('balance_greater_than_zero') and (
                        row['debit'] - row['credit']) < 0):
                    move_lines.pop(partner.id, None)
                else:
                    row['ending_bal'] = True
                    row['initial_bal'] = False
                    move_lines[partner.id]['lines'].append(row)
                    move_lines[partner.id]['debit'] = row['debit']
                    move_lines[partner.id]['credit'] = row['credit']
                    move_lines[partner.id]['balance'] = row['balance']
                    move_lines[partner.id]['company_currency_id'] = currency.id
                    move_lines[partner.id]['company_currency_symbol'] = symbol
                    move_lines[partner.id][
                        'company_currency_precision'] = rounding
                    move_lines[partner.id][
                        'company_currency_position'] = position
                    move_lines[partner.id]['count'] = len(current_lines)
                    move_lines[partner.id]['pages'] = self.get_page_list(
                        len(current_lines))
                    move_lines[partner.id]['single_page'] = True if len(
                        current_lines) <= FETCH_RANGE else False

        return move_lines

    def pl_move_lines(self, offset=0, partner=0,
                      fetch_range=FETCH_RANGE):
        # To show detailed move lines as sub lines
        cr = self.env.cr
        data = self.get_filters(default_filters={})
        offset_count = offset * fetch_range
        opening_balance = 0
        company_id = self.env.user.company_id
        currency_id = company_id.currency_id

        WHERE = '1=1'
        type = ('receivable', 'payable')
        if data.get('type'):
            type = tuple([self.type, 'none'])
            WHERE += ' AND ty.type IN %s' % str(type)

        if data.get('reconciled') == 'unreconciled':
            WHERE += ' AND l.full_reconcile_id is null AND' \
                     ' l.balance != 0 AND a.reconcile is true'

        if data.get('journal_ids', []):
            WHERE += ' AND j.id IN %s' % str(
                tuple(data.get('journal_ids')) + tuple([0]))

        if data.get('account_ids', []):
            WHERE += ' AND a.id IN %s' % str(
                tuple(data.get('account_ids')) + tuple([0]))

        if data.get('partner_ids', []):
            WHERE += ' AND p.id IN %s' % str(
                tuple(data.get('partner_ids')) + tuple([0]))

        if data.get('company_id', False):
            WHERE += ' AND l.company_id = %s' % data.get('company_id')

        if data.get('target_moves') == 'posted_only':
            WHERE += " AND m.state = 'posted'"

        if data.get('date_from') and data.get('date_to'):
            WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                'date_from') + " AND l.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND p.id = %s" % partner
        elif data.get('date_from'):
            WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get(
                'date_from')
            WHERE_CURRENT += " AND p.id = %s" % partner
        elif data.get('date_to'):
            WHERE_CURRENT = WHERE + " AND l.date <= '%s'" % data.get(
                'date_to')
            WHERE_CURRENT += " AND p.id = %s" % partner
        elif not data.get('date_from') and not data.get('date_to'):
            WHERE_CURRENT = WHERE + " AND p.id = %s" % partner
        else:
            WHERE_CURRENT = WHERE + " AND p.id = %s" % partner
        ORDER_BY_CURRENT = 'l.date'
        move_lines = []

        sql = ('''
            SELECT COUNT(*)
            FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON (a.user_type_id = ty.id )
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
            AND ty.type IN %s
        ''') % (WHERE_CURRENT, type)
        cr.execute(sql)
        count = cr.fetchone()[0]

        sql = ('''
                SELECT
                    l.id AS lid,
                    l.account_id AS account_id,
                    l.partner_id AS partner_id,
                    l.date AS ldate,
                    j.code AS lcode,
                    l.currency_id,
                    l.amount_currency,
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
                    a.name AS account_name,
                    a.code AS account_code,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON (a.user_type_id = ty.id)
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                AND ty.type IN %s
                GROUP BY l.id, l.partner_id,a.code, a.name, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.name, m.id, m.name, c.rounding, cc.id, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                ORDER BY %s
                OFFSET %s ROWS
                FETCH FIRST %s ROWS ONLY
            ''') % (
            WHERE_CURRENT, type, ORDER_BY_CURRENT, offset_count, fetch_range)
        cr.execute(sql)

        for row in cr.dictfetchall():
            move_lines.append(row)

        return count, offset_count, move_lines

    def get_xlsx_report(self, data, response, report_data, dfr_data):
        i_data = str(data)
        n_data = json.loads(i_data)
        filters = json.loads(report_data)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        cell_format = workbook.add_format(
            {'align': 'center', 'bold': True, 'bg_color': '#d3d3d3;',
             'border': 1
             })
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})

        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        sub_heading_sub = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 2,
             'border_color': 'black'})
        sheet.merge_range('A1:H2',
                          self.env.user.company_id.name + ':' + 'Partner Ledger',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})

        sheet.merge_range('A3:B3',
                          'Target Moves: ' + filters.get('target_moves'),
                          date_head)

        sheet.merge_range('C3:D3', 'Account Type: ' + filters.get('type'),
                          date_head)
        sheet.merge_range('E3:F3', ' Partners: ' + ', '.join(
            [lt or '' for lt in
             filters['partners']]), date_head)
        sheet.merge_range('G3:H3', ' Partner Type: ' + ', '.join(
            [lt or '' for lt in
             filters['categories']]),
                          date_head)
        sheet.merge_range('A4:B4', ' Journals: ' + ', '.join(
            [lt or '' for lt in
             filters['journals']]),
                          date_head)
        sheet.merge_range('C4:D4', ' Accounts: ' + ', '.join(
            [lt or '' for lt in
             filters['accounts']]),
                          date_head)

        if filters.get('date_from') and filters.get('date_to'):
            sheet.merge_range('E4:F4', 'From: ' + filters.get('date_from'),
                              date_head)

            sheet.merge_range('G4:H4', 'To: ' + filters.get('date_to'),
                              date_head)
        elif filters.get('date_from'):
            sheet.merge_range('E4:F4', 'From: ' + filters.get('date_from'),
                              date_head)
        elif filters.get('date_to'):
            sheet.merge_range('E4:F4', 'To: ' + filters.get('date_to'),
                              date_head)

        sheet.merge_range('A5:E5', 'Partner', cell_format)
        sheet.write('F5', 'Debit', cell_format)
        sheet.write('G5', 'Credit', cell_format)
        sheet.write('H5', 'Balance', cell_format)

        lst = []
        for rec in n_data:
            lst.append(rec)
        row = 4
        col = 0

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 36)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        for l_list in lst:
            one_lst = []
            two_lst = []

            if n_data[l_list]['count']:
                one_lst.append(n_data[l_list])
                two_lst = (n_data[l_list]['lines'])
                two_lst.pop()

                row += 1
                sheet.merge_range(row, col + 0, row, col + 4, n_data[l_list]['name'],
                                  sub_heading_sub)
                sheet.write(row, col + 5, n_data[l_list]['debit'], sub_heading_sub)
                sheet.write(row, col + 6, n_data[l_list]['credit'], sub_heading_sub)
                sheet.write(row, col + 7, n_data[l_list]['balance'], sub_heading_sub)
                row += 1
                sheet.write(row, col + 0, 'Date', cell_format)
                sheet.write(row, col + 1, 'JRNL', cell_format)
                sheet.write(row, col + 2, 'Account', cell_format)
                sheet.write(row, col + 3, 'Move', cell_format)
                sheet.write(row, col + 4, 'Entry Label', cell_format)
                sheet.write(row, col + 5, 'Debit', cell_format)
                sheet.write(row, col + 6, 'Credit', cell_format)
                sheet.write(row, col + 7, 'Balance', cell_format)
                for r_rec in two_lst:
                    row += 1
                    sheet.write(row, col + 0, r_rec['ldate'], txt)
                    sheet.write(row, col + 1, r_rec['lcode'], txt)
                    sheet.write(row, col + 2, r_rec['account_code'], txt)
                    sheet.write(row, col + 3, r_rec['move_name'], txt)
                    sheet.write(row, col + 4, r_rec['lname'], txt)
                    sheet.write(row, col + 5, r_rec['debit'], txt)
                    sheet.write(row, col + 6, r_rec['credit'], txt)
                    sheet.write(row, col + 7, r_rec['balance'], txt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()