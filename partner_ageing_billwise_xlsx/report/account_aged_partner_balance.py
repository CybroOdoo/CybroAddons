# -*- coding: utf-8 -*-

import time
from odoo import models,api
from datetime import datetime
from odoo import _
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo.tools import float_is_zero
from dateutil.relativedelta import relativedelta


class BillWiseBalance(models.AbstractModel):
    _name = 'report.partner_ageing_billwise_xlsx.financial_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _get_billwise_move_lines(self, account_type, date_from, target_move, period_length):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            periods[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        res = []
        total = []
        cr = self.env.cr
        company_ids = self.env.context.get('company_ids', (self.env.user.company_id.id,))
        user_company = self.env.user.company_id
        user_currency = user_company.currency_id
        ResCurrency = self.env['res.currency'].with_context(date=date_from)
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
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
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)
        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], {}, periods

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
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.amount
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'
            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
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
            for line in self.env['account.move.line'].browse(aml_ids).with_context(prefetch_fields=False):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = ResCurrency._compute(line.company_id.currency_id, user_currency, line.balance)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)
                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)
        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
        return res, total, lines, periods

    @api.model
    def generate_xlsx_report(self, workbook, data, lines):
        currency = self.env.user.company_id.currency_id.symbol or ''
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'vcenter', 'bg_color': '#D3D3D3', 'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format({'font_size': 12})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format1.set_align('center')
        format2.set_align('left')
        format3.set_align('left')
        format4.set_align('center')

        sheet.merge_range('A2:J3', 'Aged Partner Balance', format1)
        row = 5
        col = 0
        # try:
        if lines['result_selection'] == 'customer':
            account_type = ['receivable']
        elif lines['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']
        target_move = lines['target_move']

        movelines, total, dummy, periods = self._get_billwise_move_lines(account_type, lines['date_from'], target_move, lines['period_length'])
        for partner in dummy:
            for line in dummy[partner]:
                line['intervals'] = {
                    '0': 0,
                    '1': 0,
                    '2': 0,
                    '3': 0,
                    '4': 0,
                    '5': 0,
                    'total': 0
                }
                line['intervals'][str(line['period'] - 1)] = line['amount']
                line['intervals']['total'] += line['amount']

        form = lines
        sheet.merge_range(row, col, row, col+2, 'Start Date :', format2)
        sheet.merge_range(row, col+3, row, col+6, form['date_from'], format2)
        row += 1
        sheet.merge_range(row, col, row, col+2, 'Period Length (days) :', format2)
        sheet.merge_range(row, col+3, row, col+6, form['period_length'], format2)
        row += 1
        account_type = ""
        if form['result_selection'] == 'customer':
            account_type = "Receivable Accounts"
        elif lines['result_selection'] == 'supplier':
            account_type = "Payable Accounts"
        elif form['result_selection'] == 'customer_supplier':
            account_type = "Receivable & Payable Accounts"
        target_move = ""
        if form['target_move'] == 'all':
            target_move += "All Entries"
        elif form['result_selection'] == 'posted':
            target_move += "All Posted Entries"
        sheet.merge_range(row, col, row, col+2, "Partner's :", format2)
        sheet.merge_range(row, col + 3, row, col + 6, account_type, format2)
        row += 1
        sheet.merge_range(row, col, row, col+2, 'Report Type :', format2)
        sheet.merge_range(row, col+3, row, col+6,
                          "Bill-Wise", format2)
        row += 2
        # constructing the table
        sheet.merge_range(row, col, row, col+2, "Partners", format5)
        sheet.set_column(col+2, col+9, 10)
        sheet.write(row, col+3, "Not Due", format5)
        sheet.write(row, col+4, periods['4']['name'], format5)
        sheet.write(row, col+5, periods['3']['name'], format5)
        sheet.write(row, col+6, periods['2']['name'], format5)
        sheet.write(row, col+7, periods['1']['name'], format5)
        sheet.write(row, col+8, periods['0']['name'], format5)
        sheet.write(row, col+9, "Total", format5)

        row += 2
        sheet.merge_range(row, col, row, col+2, "Account Total", format3)
        if total:
            sheet.write(row, col + 3,
                        total[6] and str(total[6])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 4,
                        total[4] and str(total[4])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 5,
                        total[3] and str(total[3])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 6,
                        total[2] and str(total[2])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 7,
                        total[1] and str(total[1])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 8,
                        total[0] and str(total[0])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 9,
                        total[5] and str(total[5])+" "+currency or '__',
                        format2)

        row += 1
        for partner in movelines:
            sheet.merge_range(row, col, row, col + 2, partner['name'], format3)
            sheet.write(row, col + 3,
                        partner['direction'] and str(partner['direction'])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 4,
                        partner['4'] and str(partner['4'])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 5,
                        partner['3'] and str(partner['3'])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 6,
                        partner['2'] and str(partner['2'])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 7,
                        partner['1'] and str(partner['1'])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 8,
                        partner['0'] and str(partner['0'])+" "+currency or '__',
                        format2)
            sheet.write(row, col + 9,
                        partner['total'] and str(partner['total'])+" "+currency or '__',
                        format2)
            row += 1

            for line in dummy[partner['partner_id']]:
                if line['amount'] > 0:
                    sheet.merge_range(row, col, row, col + 2, line['line'].invoice_id.number, format4)
                    sheet.write(row, col + 3,
                                line['intervals'].get('5') and str(line['intervals'].get('5'))+" "+currency or '__',
                                format2)
                    sheet.write(row, col + 4,
                                line['intervals'].get('4') and str(line['intervals'].get('4'))+" "+currency or '__',
                                format2)
                    sheet.write(row, col + 5,
                                line['intervals'].get('3') and str(line['intervals'].get('3'))+" "+currency or '__',
                                format2)
                    sheet.write(row, col + 6,
                                line['intervals'].get('2') and str(line['intervals'].get('2'))+" "+currency or '__',
                                format2)
                    sheet.write(row, col + 7,
                                line['intervals'].get('1') and str(line['intervals'].get('1'))+" "+currency or '__',
                                format2)
                    sheet.write(row, col + 8,
                                line['intervals'].get('0') and str(line['intervals'].get('0'))+" "+currency or '__',
                                format2)
                    sheet.write(row, col + 9,
                                line['intervals'].get('total') and str(line['intervals'].get('total'))+" "+currency or '__',
                                format2)
                    row += 1
            row += 1
