"""Partner Ageing"""
import io
import json
import xlsxwriter
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

FETCH_RANGE = 2500


class PartnerAgeing(models.TransientModel):
    """ Transient class For Ageing partner"""
    _name = "dynamic.ageing.partner"

    @api.onchange('partner_type')
    def onchange_partner_type(self):
        self.partner_ids = [(5,)]
        if self.partner_type:
            company_id = self.env.user.company_id
            if self.partner_type == 'customer':
                partner_company_domain = [('parent_id', '=', False),
                                          ('customer', '=', True),
                                          '|',
                                          ('company_id', '=', company_id.id),
                                          ('company_id', '=', False)]

                self.partner_ids |= self.env['res.partner'].search \
                    (partner_company_domain)
            if self.partner_type == 'supplier':
                partner_company_domain = [('parent_id', '=', False),
                                          ('supplier', '=', True),
                                          '|',
                                          ('company_id', '=', company_id.id),
                                          ('company_id', '=', False)]

                self.partner_ids |= self.env['res.partner'].search \
                    (partner_company_domain)

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Ageing'))
        return res

    as_on_date = fields.Date(string='As on date', required=True,
                             default=fields.Date.today())
    bucket_1 = fields.Integer(string='Bucket 1', required=True, default=20)
    bucket_2 = fields.Integer(string='Bucket 2', required=True, default=40)
    bucket_3 = fields.Integer(string='Bucket 3', required=True, default=60)
    bucket_4 = fields.Integer(string='Bucket 4', required=True, default=80)
    bucket_5 = fields.Integer(string='Bucket 5', required=True, default=100)
    include_details = fields.Boolean(string='Include Details', default=True)
    type = fields.Selection([('receivable', 'Receivable Accounts Only'),
                             ('payable', 'Payable Accounts Only')],
                            string='Type')
    partner_type = fields.Selection([('customer', 'Customer Only'),
                                     ('supplier', 'Supplier Only')],
                                    string='Partner Type')

    partner_ids = fields.Many2many(
        'res.partner', required=False
    )
    partner_category_ids = fields.Many2many(
        'res.partner.category', string='Partner Tag',
    )
    target_moves = fields.Selection(
        [('draft', 'Draft'),
         ('posted', 'Posted')], default='draft', string='Target Moves'

    )
    company_id = fields.Many2one(
        'res.company', string='Company',

    )

    def write(self, vals):

        if not vals.get('partner_ids'):
            vals.update({
                'partner_ids': [(5, 0, 0)]
            })

        if vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(4, j) for j in vals.get(
                'partner_category_ids')]})
        if vals.get('partner_category_ids') == []:
            vals.update({'partner_category_ids': [(5,)]})
        ret = super(PartnerAgeing, self).write(vals)

        return ret

    def validate_data(self):
        if not (self.bucket_1 < self.bucket_2 and
                self.bucket_2 < self.bucket_3 and
                self.bucket_3 < self.bucket_4 and
                self.bucket_4 < self.bucket_5):
            raise ValidationError(_('"Bucket order must be ascending"'))
        return True

    def get_filters(self, default_filters={}):
        """ shows filters """
        company_id = self.env.user.company_id
        partner_company_domain = [('parent_id', '=', False),
                                  # '|',
                                  # ('customer_rank', '=', True),
                                  # ('supplier_rank', '=', True),
                                  '|',
                                  ('company_id', '=', company_id.id),
                                  ('company_id', '=', False)]

        partners = self.partner_ids if self.partner_ids else self.env[
            'res.partner'].search(partner_company_domain)
        categories = self.partner_category_ids if self.partner_category_ids else \
            self.env['res.partner.category'].search([])

        filter_dict = {
            'partner_ids': self.partner_ids.ids,
            'partner_category_ids': self.partner_category_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'as_on_date': self.as_on_date,
            'type': self.type,
            'target_moves': self.target_moves,
            'partner_type': self.partner_type,
            'bucket_1': self.bucket_1,
            'bucket_2': self.bucket_2,
            'bucket_3': self.bucket_3,
            'bucket_4': self.bucket_4,
            'bucket_5': self.bucket_5,
            'include_details': self.include_details,

            'partners_list': [(p.id, p.name) for p in partners],
            'category_list': [(c.id, c.name) for c in categories],
            'company_name': self.company_id and self.company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})
        filters = {}
        filters['bucket_1'] = data.get('bucket_1')
        filters['bucket_2'] = data.get('bucket_2')
        filters['bucket_3'] = data.get('bucket_3')
        filters['bucket_4'] = data.get('bucket_4')
        filters['bucket_5'] = data.get('bucket_5')

        if data.get('partner_ids', []):
            filters['partners'] = self.env['res.partner'].browse(
                data.get('partner_ids', [])).mapped('name')
        else:
            filters['partners'] = ['All']

        if data.get('as_on_date', False):
            filters['as_on_date'] = data.get('as_on_date')

        if data.get('company_id'):
            filters['company_id'] = data.get('company_id')
        else:
            filters['company_id'] = ''

        if data.get('target_moves') == 'draft':

            filters['target_moves'] = 'All Entries'
        else:
            filters['target_moves'] = 'Posted Only'

        if data.get('type') == 'receivable':
            filters['type'] = 'Receivable'
        elif data.get('type') == 'payable':
            filters['type'] = 'Payable'
        else:
            filters['type'] = 'Receivable and Payable'

        if data.get('partner_type') == 'customer':
            filters['partner_type'] = 'Customer Only'
        elif data.get('partner_type') == 'supplier':
            filters['partner_type'] = 'Supplier Only'
        else:
            filters['partner_type'] = 'Customer And Supplier '

        if data.get('partner_category_ids', []):
            filters['categories'] = self.env['res.partner.category'].browse(
                data.get('partner_category_ids', [])).mapped('name')
        else:
            filters['categories'] = ['All']

        if data.get('include_details'):
            filters['include_details'] = True
        else:
            filters['include_details'] = False

        filters['partners_list'] = data.get('partners_list')
        filters['category_list'] = data.get('category_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def prepare_bucket_list(self):
        """ prepare bucket values for partner ageing report"""
        periods = {}
        date_from = self.as_on_date
        date_from = fields.Date.from_string(date_from)
        bucket_list = [self.bucket_1, self.bucket_2, self.bucket_3,
                       self.bucket_4, self.bucket_5]
        start = False
        stop = date_from
        name = 'Not'
        periods[0] = {
            'bucket': 'As on',
            'name': name,
            'start': '',
            'stop': stop.strftime('%Y-%m-%d'),
        }

        stop = date_from
        final_date = False
        for i in range(5):
            start = stop - relativedelta(days=1)
            stop = start - relativedelta(days=bucket_list[i])
            name = 'value_' + str(bucket_list[0]) if i == 0 else str(
                str(bucket_list[i - 1] + 1)) + str(bucket_list[i])

            final_date = stop
            periods[i + 1] = {
                'bucket': bucket_list[i],
                'name': name,
                'start': start.strftime('%Y-%m-%d'),
                'stop': stop.strftime('%Y-%m-%d'),
            }

        start = final_date - relativedelta(days=1)
        stop = ''
        name = str(self.bucket_5)

        periods[6] = {
            'bucket': 'Above',
            'name': name,
            'start': start.strftime('%Y-%m-%d'),
            'stop': '',
        }
        return periods

    def al_move_lines(self, offset=0, partner=0, fetch_range=FETCH_RANGE):
        """ shows detailed move lines"""

        as_on_date = self.as_on_date
        period_dict = self.prepare_bucket_list()
        period_list = [period_dict[a]['name'] for a in period_dict]
        company_id = self.env.user.company_id
        type = ('receivable', 'payable')
        if self.type:
            type = tuple([self.type, 'none'])
        arg_list = ('draft', 'posted')
        if self.target_moves == 'posted':
            arg_list = tuple([self.target_moves, 'none'])
        offset = offset * fetch_range
        count = 0
        move_lines = []
        if partner:
            sql = """
                    SELECT COUNT(*)
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    WHERE
                        l.balance <> 0
                        AND m.state IN %s
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                """ % (arg_list, type, partner, as_on_date, company_id.id)
            self.env.cr.execute(sql)
            count = self.env.cr.fetchone()[0]

            SELECT = """SELECT m.name AS move_name,
                                m.id AS move_id,
                                l.date AS date,
                                l.date_maturity AS date_maturity, 
                                j.name AS journal_name,
                                cc.id AS company_currency_id,
                                a.name AS account_name,
                                a.code AS account_code,
                                c.symbol AS currency_symbol,
                                c.position AS currency_position,
                                c.rounding AS currency_precision,
                                cc.id AS company_currency_id,
                                cc.symbol AS company_currency_symbol,
                                cc.rounding AS company_currency_precision,
                                cc.position AS company_currency_position,"""

            for period in period_dict:
                if period_dict[period].get('start') and period_dict[period].get(
                        'stop'):
                    SELECT += """ CASE
                                    WHEN 
                                        COALESCE(l.date_maturity,l.date) >= '%s' AND 
                                        COALESCE(l.date_maturity,l.date) <= '%s'
                                    THEN
                                        sum(l.balance) +
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s,""" % (
                        period_dict[period].get('stop'),
                        period_dict[period].get('start'),
                        as_on_date,
                        as_on_date,
                        'range_' + str(period),
                    )
                elif not period_dict[period].get('start'):
                    SELECT += """ CASE
                                    WHEN 
                                        COALESCE(l.date_maturity,l.date) >= '%s' 
                                    THEN
                                        sum(
                                            l.balance
                                            ) +
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s,""" % (
                        period_dict[period].get('stop'), as_on_date, as_on_date,
                        'range_' + str(period))
                else:
                    SELECT += """ CASE
                                    WHEN
                                        COALESCE(l.date_maturity,l.date) <= '%s' 
                                    THEN
                                        sum(
                                            l.balance
                                            ) +
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s """ % (
                        period_dict[period].get('start'), as_on_date,
                        as_on_date,
                        'range_' + str(period))

            sql = """

                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    LEFT JOIN 
                        res_currency AS c ON l.currency_id = c.id    
                    LEFT JOIN 
                        res_currency AS cc ON l.company_currency_id = cc.id
                    WHERE
                        l.balance <> 0
                        AND m.state IN %s
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                    GROUP BY
                        l.date, l.date_maturity,l.currency_id, m.id, m.name, j.name, a.name,a.code, c.rounding, cc.id, cc.rounding, cc.position, c.position, c.symbol, cc.symbol
                    OFFSET %s ROWS
                    FETCH FIRST %s ROWS ONLY
                """ % (
                arg_list, type, partner, as_on_date, company_id.id, offset, fetch_range)
            self.env.cr.execute(SELECT + sql)
            final_list = self.env.cr.dictfetchall() or 0.0

            for m_list in final_list:
                if (m_list['range_0'] or m_list['range_1'] or m_list['range_2'] or
                        m_list['range_3'] or m_list['range_4'] or m_list['range_5']):
                    move_lines.append(m_list)
        return count, offset, move_lines, period_list

    def report_data(self):
        """ fetch values from query to get report, prepare bucket values """
        data = self.get_filters(default_filters={})

        period_dict = self.prepare_bucket_list()
        company_id = self.env.user.company_id
        domain = ['|', ('company_id', '=', company_id.id),
                  ('company_id', '=', False)]
        if self.partner_type == 'customer':
            domain.append(('customer_rank', '=', True))
        if self.partner_type == 'supplier':
            domain.append(('supplier_rank', '=', True))

        if self.partner_category_ids:
            domain.append(('category_id', 'in', self.partner_category_ids.ids))

        partner_ids = self.partner_ids or self.env['res.partner'].search(domain)
        as_on_date = self.as_on_date
        company_currency_id = company_id.currency_id.id
        company_currency_symbol = company_id.currency_id.symbol
        company_currency_position = company_id.currency_id.position
        company_currency_precision = company_id.currency_id.rounding

        type = ('receivable', 'payable')
        if self.type:
            type = tuple([self.type, 'none'])
        arg_list = ('draft', 'posted')
        if self.target_moves == 'posted':
            arg_list = tuple([self.target_moves, 'none'])

        partner_dict = {}
        for partner in partner_ids:
            partner_dict.update({partner.id: {}})

        for partner in partner_ids:
            partner_dict[partner.id].update(
                {'id': partner.id, 'partner_name': partner.name})

            total_balance = 0.0
            sql = """
                SELECT

                    COUNT(*) AS count
                FROM
                    account_move_line AS l
                LEFT JOIN
                    account_move AS m ON m.id = l.move_id
                LEFT JOIN
                    account_account AS a ON a.id = l.account_id
                LEFT JOIN
                    account_account_type AS ty ON a.user_type_id = ty.id
                WHERE 
                    l.balance <> 0
                    AND m.state IN %s
                    AND ty.type IN %s
                    AND l.partner_id = %s
                    AND l.date <= '%s'
                    AND l.company_id = %s
            """ % (arg_list, type, partner.id, as_on_date, company_id.id)
            self.env.cr.execute(sql)

            fetch_dict = self.env.cr.dictfetchone() or 0.0

            count = fetch_dict.get('count') or 0.0

            if count:
                for period in period_dict:

                    where = " AND l.date <= '%s' AND l.partner_id = %s " \
                            "AND COALESCE(l.date_maturity,l.date) " % (
                                as_on_date, partner.id)
                    if period_dict[period].get('start') and period_dict[
                        period].get('stop'):
                        where += " BETWEEN '%s' AND '%s'" % (
                            period_dict[period].get('stop'),
                            period_dict[period].get('start'))
                    elif not period_dict[period].get('start'):  # ie just
                        where += " >= '%s'" % (period_dict[period].get('stop'))
                    else:
                        where += " <= '%s'" % (period_dict[period].get('start'))

                    sql = """
                        SELECT
                            sum(l.balance) AS balance,
                            sum(COALESCE((SELECT SUM(amount)FROM account_partial_reconcile
                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_debit,
                            sum(COALESCE((SELECT SUM(amount) FROM account_partial_reconcile 
                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_credit
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        WHERE 
                            l.balance <> 0

                            AND ty.type IN %s
                            AND m.state IN %s
                            AND l.company_id = %s
                    """ % (as_on_date, as_on_date, type, arg_list, company_id.id)
                    amount = 0.0
                    self.env.cr.execute(sql + where)

                    fetch_dict = self.env.cr.dictfetchall() or 0.0

                    if not fetch_dict[0].get('balance'):
                        amount = 0.0
                    else:
                        amount = fetch_dict[0]['balance'] + fetch_dict[0][
                            'sum_debit'] - fetch_dict[0]['sum_credit']
                        total_balance += amount

                    partner_dict[partner.id].update(
                        {period_dict[period]['name']: amount})

                partner_dict[partner.id].update({'count': count})

                partner_dict[partner.id].update(
                    {'pages': self.get_page_list(count)})
                partner_dict[partner.id].update(
                    {'single_page': True if count <= FETCH_RANGE else False})
                partner_dict[partner.id].update({'total': total_balance})
                partner_dict[partner.id].update(
                    {'company_currency_id': company_currency_id})
                partner_dict[partner.id].update(
                    {'company_currency_symbol': company_currency_symbol})
                partner_dict[partner.id].update(
                    {'company_currency_position': company_currency_position})
                partner_dict[partner.id].update(
                    {'company_currency_precision': company_currency_precision})
                partner_dict[partner.id].update(
                    {'partner_move_lines': self.al_move_lines(0, partner.id,
                                                              2500)})

            else:
                partner_dict.pop(partner.id, None)

        return period_dict, partner_dict

    def get_page_list(self, total_count):
        '''
        Helper function to get list of pages from total_count
        :param total_count: integer
        :return: list(pages) eg. [1,2,3,4,5,6,7 ....]
        '''
        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i + 1 for i in range(0, int(page_count))] or []

    def get_data(self, default_filters={}, data=None):
        """ return period list and filters"""
        filters = self.process_filters()
        period_dict, partner_lines = self.report_data()
        period_list = [period_dict[a]['name'] for a in period_dict]
        return filters, partner_lines, period_dict, period_list

    def get_xlsx_report(self, data, response, report_data, dfr_data):
        """ xlsx report of Partner Ageing"""

        i_data = str(data)
        n_data = json.loads(i_data)
        filters = json.loads(report_data)
        output = io.BytesIO()
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
        sheet.merge_range('E1:I2',
                          self.env.user.company_id.name + ':' + ' Partner Ageing',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        sheet.merge_range('A3:C3', 'As On Date: ' + filters.get('as_on_date'),
                          date_head)
        sheet.merge_range('D3:F3', 'Account Type: ' + filters.get('type'), date_head)
        sheet.merge_range('G3:H3', 'Target Moves: ' + filters.get('target_moves'),
                          date_head)
        sheet.merge_range('I3:J3',
                          'Partner Type: ' + filters.get('partner_type'),
                          date_head)
        sheet.merge_range('D4:F4', '  Partners: ' + ', '.join(
            [lt or '' for lt in
             filters['partners']]), date_head)
        sheet.merge_range('G4:H4', ' Partner Type: ' + ', '.join(
            [lt or '' for lt in
             filters['categories']]),
                          date_head)
        sheet.merge_range('A5:C5', 'Partner', cell_format)
        sheet.write('D5', 'Total', cell_format)
        sheet.write('E5', 'Not Due', cell_format)
        sheet.write('F5', '0-20', cell_format)
        sheet.write('G5', '21-40', cell_format)
        sheet.write('H5', '41-60', cell_format)
        sheet.write('I5', '61-80', cell_format)
        sheet.write('J5', '81-100', cell_format)
        sheet.write('K5', '100+', cell_format)

        lst = []
        for rec in n_data:
            lst.append(rec)
        row = 4
        col = 0
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 26)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 26)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)

        for l_rec in lst:
            one_lst = []
            two_lst = []

            if n_data[l_rec]['count']:
                one_lst.append(n_data[l_rec])
                two_lst = (n_data[l_rec]['partner_move_lines'][2])
                sheet.merge_range(row + 1, col, row + 1, col + 2,
                                  n_data[l_rec]['partner_name'], sub_heading_sub)
                sheet.write(row + 1, col + 3, n_data[l_rec]['total'], sub_heading_sub)
                sheet.write(row + 1, col + 4, n_data[l_rec]['Not'], sub_heading_sub)
                sheet.write(row + 1, col + 5, n_data[l_rec]['value_20'], sub_heading_sub)
                sheet.write(row + 1, col + 6, n_data[l_rec]['2140'], sub_heading_sub)
                sheet.write(row + 1, col + 7, n_data[l_rec]['4160'], sub_heading_sub)
                sheet.write(row + 1, col + 8, n_data[l_rec]['6180'], sub_heading_sub)
                sheet.write(row + 1, col + 9, n_data[l_rec]['81100'], sub_heading_sub)
                sheet.write(row + 1, col + 10, n_data[l_rec]['100'], sub_heading_sub)

                row += 2
                sheet.write(row, col, 'Entry Label', cell_format)
                sheet.write(row, col + 1, 'Due Date', cell_format)
                sheet.write(row, col + 2, 'Journal', cell_format)
                sheet.write(row, col + 3, 'Account', cell_format)
                sheet.write(row, col + 4, 'Not Due', cell_format)
                sheet.write(row, col + 5, '0 - 20', cell_format)
                sheet.write(row, col + 6, '21 - 40', cell_format)
                sheet.write(row, col + 7, '41 - 60', cell_format)
                sheet.write(row, col + 8, '61 - 80', cell_format)
                sheet.write(row, col + 9, '81 - 100', cell_format)
                sheet.write(row, col + 10, '100 +', cell_format)
                for r_rec in two_lst:
                    row += 1
                    sheet.write(row, col, r_rec['move_name'], txt)
                    sheet.write(row, col + 1, r_rec['date_maturity'], txt)
                    sheet.write(row, col + 2, r_rec['journal_name'], txt)
                    sheet.write(row, col + 3, r_rec['account_code'], txt)
                    sheet.write(row, col + 4, r_rec['range_0'], txt)
                    sheet.write(row, col + 5, r_rec['range_1'], txt)
                    sheet.write(row, col + 6, r_rec['range_2'], txt)
                    sheet.write(row, col + 7, r_rec['range_3'], txt)
                    sheet.write(row, col + 8, r_rec['range_4'], txt)
                    sheet.write(row, col + 9, r_rec['range_5'], txt)
                    sheet.write(row, col + 10, r_rec['range_6'], txt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
