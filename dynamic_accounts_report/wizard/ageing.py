import time
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.tools import float_is_zero

import io
import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AgeingView(models.TransientModel):
    _inherit = "account.common.report"
    _name = 'account.partner.ageing'

    period_length = fields.Integer(string='Period Length (days)',
                                   required=True, default=30)
    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))
    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                         ('supplier', 'Payable Accounts'),
                                         ('customer_supplier',
                                          'Receivable and Payable Accounts')
                                         ], string="Partner's", required=True,
                                        default='customer')

    partner_ids = fields.Many2many(
        'res.partner', string='Partner'
    )
    partner_category_ids = fields.Many2many(
        'res.partner.category', string='Partner Tag',
    )

    @api.model
    def view_report(self, option):
        r = self.env['account.partner.ageing'].search([('id', '=', option[0])])

        data = {
            'result_selection': r.result_selection,
            'model': self,
            'journals': r.journal_ids,
            'target_move': r.target_move,
            'period_length': r.period_length,
            'partners': r.partner_ids,
            'partner_tags': r.partner_category_ids,

        }
        if r.date_from:
            data.update({
                'date_from': r.date_from,
            })

        filters = self.get_filter(option)

        records = self._get_report_values(data)

        currency = self._get_currency()

        return {
            'name': "Partner Ageing",
            'type': 'ir.actions.client',
            'tag': 'p_a',
            'filters': filters,
            'report_lines': records['Partners'],
            'currency': currency,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}

        if data.get('target_move'):
            filters['target_move'] = data.get('target_move')
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('result_selection') == 'customer':
            filters['result_selection'] = 'Receivable'
        elif data.get('result_selection') == 'supplier':
            filters['result_selection'] = 'Payable'
        else:
            filters['result_selection'] = 'Receivable and Payable'

        if data.get('partners'):
            filters['partners'] = self.env['res.partner'].browse(
                data.get('partners')).mapped('name')
        else:
            filters['partners'] = ['All']

        if data.get('partner_tags', []):
            filters['partner_tags'] = self.env['res.partner.category'].browse(
                data.get('partner_tags', [])).mapped('name')
        else:
            filters['partner_tags'] = ['All']

        filters['company_id'] = ''
        filters['company_name'] = data.get('company_name')
        filters['partners_list'] = data.get('partners_list')
        filters['category_list'] = data.get('category_list')
        filters['company_name'] = data.get('company_name')
        filters['target_move'] = data.get('target_move').capitalize()


        return filters

    def get_filter_data(self, option):
        r = self.env['account.partner.ageing'].search([('id', '=', option[0])])
        default_filters = {}
        company_id = self.env.companies
        company_domain = [('company_id', 'in', company_id.ids)]
        partner = r.partner_ids if r.partner_ids else self.env[
            'res.partner'].search([])
        categories = r.partner_category_ids if r.partner_category_ids \
            else self.env['res.partner.category'].search([])

        filter_dict = {
            'partners': r.partner_ids.ids,
            'partner_tags': r.partner_category_ids.ids,
            'company_id': company_id.ids,
            'date_from': r.date_from,

            'target_move': r.target_move,
            'result_selection': r.result_selection,
            'partners_list': [(p.id, p.name) for p in partner],
            'category_list': [(c.id, c.name) for c in categories],
            'company_name': ', '.join(self.env.companies.mapped('name')),
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_values(self, data):
        docs = data['model']
        date_from = data.get('date_from').strftime('%Y-%m-%d')
        if data['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']
        target_move = data['target_move']
        partners = data.get('partners')
        if data['partner_tags']:
            partners = self.env['res.partner'].search(
                [('category_id', 'in', data['partner_tags'].ids)])

        account_res = self._get_partner_move_lines(data, partners, date_from,
                                                   target_move,
                                                   account_type,
                                                   data['period_length'])

        return {
            'doc_ids': self.ids,
            'docs': docs,
            'time': time,
            'Partners': account_res,

        }

    @api.model
    def create(self, vals):
        vals['target_move'] = 'posted'
        res = super(AgeingView, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('target_move'):
            vals.update({'target_move': vals.get('target_move').lower()})

        if vals.get('partner_ids'):
            vals.update(
                {'partner_ids': [(4, j) for j in vals.get('partner_ids')]})
        if not vals.get('partner_ids'):
            vals.update({'partner_ids': [(5,)]})
        if vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(4, j) for j in vals.get(
                'partner_category_ids')]})
        if not vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(5,)]})

        res = super(AgeingView, self).write(vals)
        return res

    def _get_partner_move_lines(self, data, partners, date_from, target_move,
                                account_type,
                                period_length):

        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5 - (i + 1)) * period_length + 1) + '-' + str(
                (5 - i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop
        res = []
        total = []
        cr = self.env.cr
        user_company = self.env.company

        user_currency = user_company.currency_id
        ResCurrency = self.env['res.currency'].with_context(date=date_from)
        # company_ids = self._context.get('company_ids') or [user_company.id]

        company_ids = self.env.companies.ids
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))

        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute(
            'SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where max_date > %s',
            (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids),)
        partner_list = '(l.partner_id IS NOT  NULL)'
        if partners:
            list = tuple(partners.ids) + tuple([0])
            if list:
                partner_list = '(l.partner_id IS NULL OR l.partner_id IN %s)'
                arg_list += (tuple(list),)
        query = '''
                    SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
                    FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
                    WHERE (l.account_id = account_account.id)
                        AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                       
                        AND ''' + reconciliation_clause + '''          
                        AND (l.date <= %s)
                        AND l.company_id IN %s
                        AND ''' + partner_list + '''
                           
                    ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)


        partners = cr.dictfetchall()

        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if
                       partner['partner_id']]

        lines = dict(
            (partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                        FROM account_move_line AS l, account_account, account_move am
                        WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                            AND (am.state IN %s)
                            AND (account_account.internal_type IN %s)
                            AND (COALESCE(l.date_maturity,l.date) >= %s)\
                            AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND (l.date <= %s)
                        AND l.company_id IN %s'''
        cr.execute(query, (
            tuple(move_state), tuple(account_type), date_from,
            tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            move_id = line.move_id.id
            move_name = line.move_id.name
            date_maturity = line.date_maturity
            account_id = line.account_id.name
            account_code = line.account_id.code
            jrnl_id = line.journal_id.name
            currency_id = line.company_id.currency_id.position
            currency_symbol = line.company_id.currency_id.symbol

            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = ResCurrency._compute(line.company_id.currency_id,
                                               user_currency, line.balance)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += ResCurrency._compute(
                        partial_line.company_id.currency_id, user_currency,
                        partial_line.amount)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= ResCurrency._compute(
                        partial_line.company_id.currency_id, user_currency,
                        partial_line.amount)
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'partner_id': partner_id,
                    'move': move_name,
                    'jrnl': jrnl_id,
                    'currency': currency_id,
                    'symbol': currency_symbol,
                    'acc_name': account_id,
                    'mov_id': move_id,
                    'acc_code': account_code,
                    'date': date_maturity,
                    'amount': line_amount,
                    'period6': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (
                tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'

                args_list += (
                    periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'

                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)

            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                            FROM account_move_line AS l, account_account, account_move am
                            WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                                AND (am.state IN %s)
                                AND (account_account.internal_type IN %s)
                                AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                                AND ''' + dates_query + '''
                                
                                
                            AND (l.date <= %s)
                            AND l.company_id IN %s'''
            cr.execute(query, args_list)

            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                move_id = line.move_id.id
                move_name = line.move_id.name
                date_maturity = line.date_maturity
                account_id = line.account_id.name
                account_code = line.account_id.code
                jrnl_id = line.journal_id.name
                currency_id = line.company_id.currency_id.position
                currency_symbol = line.company_id.currency_id.symbol
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = ResCurrency._compute(line.company_id.currency_id,
                                                   user_currency, line.balance)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += ResCurrency._compute(
                            partial_line.company_id.currency_id, user_currency,
                            partial_line.amount)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= ResCurrency._compute(
                            partial_line.company_id.currency_id, user_currency,
                            partial_line.amount)

                if not self.env.company.currency_id.is_zero(
                        line_amount):
                    partners_amount[partner_id] += line_amount
                    if i + 1 == 5:
                        period5 = i + 1
                        if partner_id:
                            lines[partner_id].append({
                                'period5': period5,
                                'line': line,
                                'partner_id': partner_id,
                                'move': move_name,
                                'currency': currency_id,
                                'symbol': currency_symbol,
                                'jrnl': jrnl_id,
                                'acc_name': account_id,
                                'mov_id': move_id,
                                'acc_code': account_code,
                                'date': date_maturity,
                                'amount': line_amount,
                            })
                    elif i + 1 == 4:
                        period4 = i + 1
                        if partner_id:
                            lines[partner_id].append({

                                'period4': period4,
                                'line': line,
                                'partner_id': partner_id,
                                'move': move_name,
                                'jrnl': jrnl_id,
                                'acc_name': account_id,
                                'currency': currency_id,
                                'symbol': currency_symbol,
                                'mov_id': move_id,
                                'acc_code': account_code,
                                'date': date_maturity,
                                'amount': line_amount,
                            })
                    elif i + 1 == 3:
                        period3 = i + 1
                        if partner_id:
                            lines[partner_id].append({

                                'period3': period3,
                                'line': line,
                                'partner_id': partner_id,
                                'move': move_name,
                                'jrnl': jrnl_id,
                                'acc_name': account_id,
                                'currency': currency_id,
                                'symbol': currency_symbol,
                                'mov_id': move_id,
                                'acc_code': account_code,
                                'date': date_maturity,
                                'amount': line_amount,
                            })
                    elif i + 1 == 2:
                        period2 = i + 1
                        if partner_id:
                            lines[partner_id].append({

                                'period2': period2,
                                'line': line,
                                'partner_id': partner_id,
                                'move': move_name,
                                'jrnl': jrnl_id,
                                'acc_name': account_id,
                                'currency': currency_id,
                                'symbol': currency_symbol,
                                'mov_id': move_id,
                                'acc_code': account_code,
                                'date': date_maturity,
                                'amount': line_amount,
                            })
                    else:
                        period1 = i + 1
                        if partner_id:
                            lines[partner_id].append({

                                'period1': period1,
                                'line': line,
                                'partner_id': partner_id,
                                'move': move_name,
                                'jrnl': jrnl_id,
                                'acc_name': account_id,
                                'currency': currency_id,
                                'symbol': currency_symbol,
                                'mov_id': move_id,
                                'acc_code': account_code,
                                'date': date_maturity,
                                'amount': line_amount,
                            })

            history.append(partners_amount)

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner[
                'partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            for rec in lines:
                if partner['partner_id'] == rec:
                    child_lines = lines[rec]
            values['child_lines'] = child_lines
            if not float_is_zero(values['direction'],
                                 precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)],
                                     precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum(
                [values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(
                    partner['partner_id'])
                values['name'] = browsed_partner.name and len(
                    browsed_partner.name) >= 45 and browsed_partner.name[
                                                    0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (
                    self._context.get('include_nullified_amount') and lines[
                partner['partner_id']]):
                res.append(values)

        return res, total, lines

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

    def get_dynamic_xlsx_report(self, data, response, report_data, dfr_data ):

        report_data_main = json.loads(report_data)
        output = io.BytesIO()

        filters = json.loads(data)

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 2,
             'border_color': 'black'})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_l = workbook.add_format(
            {'font_size': '10px', 'border': 1, 'bold': True})
        txt_v = workbook.add_format(
            {'align': 'right', 'font_size': '10px', 'border': 1})
        sheet.merge_range('A2:H3',
                          filters.get('company_name') + ':' + ' Partner Ageing',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})
        if filters.get('date_from'):
            sheet.merge_range('A4:B4',
                              'As On Date: ' + filters.get('date_from'),
                              date_head)
        sheet.merge_range('C4:E4',
                          'Account Type: ' + filters.get('result_selection'),
                          date_head)
        sheet.merge_range('A5:B5',
                          'Target Moves: ' + filters.get('target_move'),
                          date_head)
        sheet.merge_range('D5:F5', '  Partners: ' + ', '.join(
            [lt or '' for lt in
             filters['partners']]), date_head)
        sheet.merge_range('G5:H5', ' Partner Type: ' + ', '.join(
            [lt or '' for lt in
             filters['partner_tags']]),
                          date_head)

        sheet.merge_range('A7:C7', 'Partner', heading)
        sheet.write('D7', 'Total', heading)
        sheet.write('E7', 'Not Due', heading)
        sheet.write('F7', '0-30', heading)
        sheet.write('G7', '30-60', heading)
        sheet.write('H7', '60-90', heading)
        sheet.write('I7', '90-120', heading)
        sheet.write('J7', '120+', heading)

        lst = []
        for rec in report_data_main[0]:
            lst.append(rec)
        row = 6
        col = 0
        sheet.set_column(5, 0, 15)
        sheet.set_column(6, 1, 15)
        sheet.set_column(7, 2, 15)
        sheet.set_column(8, 3, 15)
        sheet.set_column(9, 4, 15)
        sheet.set_column(10, 5, 15)
        sheet.set_column(11, 6, 15)

        for rec_data in report_data_main[0]:
            one_lst = []
            two_lst = []

            row += 1
            sheet.merge_range(row, col, row, col + 2, rec_data['name'], txt_l)
            sheet.write(row, col + 3, rec_data['total'], txt_l)
            sheet.write(row, col + 4, rec_data['direction'], txt_l)
            sheet.write(row, col + 5, rec_data['4'], txt_l)
            sheet.write(row, col + 6, rec_data['3'], txt_l)
            sheet.write(row, col + 7, rec_data['2'], txt_l)
            sheet.write(row, col + 8, rec_data['1'], txt_l)
            sheet.write(row, col + 9, rec_data['0'], txt_l)
            row += 1
            sheet.write(row, col, 'Entry Label', sub_heading)
            sheet.write(row, col + 1, 'Due Date', sub_heading)
            sheet.write(row, col + 2, 'Journal', sub_heading)
            sheet.write(row, col + 3, 'Account', sub_heading)
            sheet.write(row, col + 4, 'Not Due', sub_heading)
            sheet.write(row, col + 5, '0 - 30', sub_heading)
            sheet.write(row, col + 6, '30 - 60', sub_heading)
            sheet.write(row, col + 7, '60 - 90', sub_heading)
            sheet.write(row, col + 8, '90 - 120', sub_heading)
            sheet.write(row, col + 9, '120 +', sub_heading)

            for line_data in rec_data['child_lines']:
                row += 1
                sheet.write(row, col, line_data.get('move'), txt)
                sheet.write(row, col + 1, line_data.get('date'), txt)
                sheet.write(row, col + 2, line_data.get('jrnl'), txt)
                sheet.write(row, col + 3, line_data.get('acc_code'), txt)
                if line_data.get('period6'):
                    sheet.write(row, col + 4, line_data.get('amount'), txt)
                else:
                    sheet.write(row, col + 4, "0", txt_v)
                if line_data.get('period5'):
                    sheet.write(row, col + 5, line_data.get('amount'), txt)
                else:
                    sheet.write(row, col + 5, "0", txt_v)
                if line_data.get('period4'):
                    sheet.write(row, col + 6, line_data.get('amount'), txt)
                else:
                    sheet.write(row, col + 6, "0", txt_v)
                if line_data.get('period3'):
                    sheet.write(row, col + 7, line_data.get('amount'), txt)
                else:
                    sheet.write(row, col + 7, "0", txt_v)
                if line_data.get('period2'):
                    sheet.write(row, col + 8, line_data.get('amount'), txt)
                else:
                    sheet.write(row, col + 8, "0", txt_v)
                if line_data.get('period1'):
                    sheet.write(row, col + 9, line_data.get('amount'), txt)
                else:
                    sheet.write(row, col + 9, "0", txt_v)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
