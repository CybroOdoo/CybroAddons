# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Haseen (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import io
import json
import xlsxwriter
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import date_utils


class Partner(models.Model):
    """ Class for adding report options  in 'res.partner' """
    _inherit = 'res.partner'

    customer_report_ids = fields.Many2many(
        'account.move',
        compute='_compute_customer_report_ids',
        help='Partner Invoices related to Customer')
    vendor_statement_ids = fields.Many2many(
        'account.move',
        compute='_compute_vendor_statement_ids',
        help='Partner Bills related to Vendor')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id.id,
        help="currency related to Customer or Vendor"
    )

    def _compute_customer_report_ids(self):
        """ For computing 'invoices' of partner"""
        for rec in self:
            inv_ids = self.env['account.move'].search(
                [('partner_id', '=', rec.id),
                 ('move_type', '=', 'out_invoice'),
                 ('payment_state', '!=', 'paid'),
                 ('state', '=', 'posted')])
            rec.customer_report_ids = inv_ids

    def _compute_vendor_statement_ids(self):
        """ For computing 'bills' of partner """
        for rec in self:
            bills = self.env['account.move'].search(
                [('partner_id', '=', rec.id),
                 ('move_type', '=', 'in_invoice'),
                 ('payment_state', '!=', 'paid'),
                 ('state', '=', 'posted')])
            rec.vendor_statement_ids = bills

    def main_query(self):
        """Return select query"""
        query = """SELECT name , invoice_date, invoice_date_due,
                    amount_total_signed AS sub_total,
                    amount_residual_signed AS amount_due ,
                    amount_residual AS balance
            FROM account_move WHERE payment_state != 'paid'
            AND state ='posted' AND partner_id= '%s'
            AND company_id = '%s' """ % (self.id, self.env.company.id)
        return query

    def amount_query(self):
        """Return query for calculating total amount"""
        amount_query = """ SELECT SUM(amount_total_signed) AS total, 
                    SUM(amount_residual) AS balance
                FROM account_move WHERE payment_state != 'paid' 
                AND state ='posted' AND partner_id= '%s'
                AND company_id = '%s' """ % (self.id, self.env.company.id)
        return amount_query

    def action_share_pdf(self):
        """ Action for sharing customer pdf report"""
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()

            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            report = self.env[
                'ir.actions.report'
            ].sudo()._render_qweb_pdf(
                'statement_report.res_partner_action',
                self, data=data)
            data_record = base64.b64encode(report[0])
            ir_values = {
                'name': 'Statement Report',
                'type': 'binary',
                'datas': data_record,
                'mimetype': 'application/pdf',
                'res_model': 'res.partner'
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached your '
                             'payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    def action_print_pdf(self):
        """ Action for printing pdf report"""
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return self.env.ref('statement_report.res_partner_action'
                                ).report_action(self, data=data)
        else:
            raise ValidationError('There is no statement to print')

    def action_print_xlsx(self):
        """ Action for printing xlsx report of customer """
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return {
                'type': 'ir.actions.report',
                'data': {
                    'model': 'res.partner',
                    'options': json.dumps(data,
                                          default=date_utils.json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Payment Statement Report'
                },
                'report_type': 'xlsx',
            }
        else:
            raise ValidationError('There is no statement to print')

    def get_xlsx_report(self, data, response):
        """ Get xlsx report data """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format_with_color = workbook.add_format({
            'font_size': '14px', 'bold': True,
            'bg_color': 'yellow', 'border': 1})
        cell_format = workbook.add_format({'font_size': '14px', 'bold': True})
        txt = workbook.add_format({'font_size': '13px'})
        txt_border = workbook.add_format({'font_size': '13px', 'border': 1})
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '22px'})
        sheet.merge_range('B2:Q4', 'Payment Statement Report', head)

        if data['customer']:
            sheet.merge_range('B7:D7', 'Customer/Supplier : ', cell_format)
            sheet.merge_range('E7:H7', data['customer'], txt)
        sheet.merge_range('B9:C9', 'Address : ', cell_format)
        if data['street']:
            sheet.merge_range('D9:F9', data['street'], txt)
        if data['street2']:
            sheet.merge_range('D10:F10', data['street2'], txt)
        if data['city']:
            sheet.merge_range('D11:F11', data['city'], txt)
        if data['state']:
            sheet.merge_range('D12:F12', data['state'], )
        if data['zip']:
            sheet.merge_range('D13:F13', data['zip'], txt)

        sheet.merge_range('B15:C15', 'Date', cell_format_with_color)
        sheet.merge_range('D15:G15', 'Invoice/Bill Number',
                          cell_format_with_color)
        sheet.merge_range('H15:I15', 'Due Date', cell_format_with_color)
        sheet.merge_range('J15:L15', 'Invoices/Debit', cell_format_with_color)
        sheet.merge_range('M15:O15', 'Amount Due', cell_format_with_color)
        sheet.merge_range('P15:R15', 'Balance Due', cell_format_with_color)

        row = 15
        column = 0
        for record in data['my_data']:
            sub_total = data['currency'] + str(record['sub_total'])
            amount_due = data['currency'] + str(record['amount_due'])
            balance = data['currency'] + str(record['balance'])
            total = data['currency'] + str(data['total'])
            remain_balance = data['currency'] + str(data['balance'])
            sheet.merge_range(row, column + 1, row, column + 2,
                              record['invoice_date'], txt_border)
            sheet.merge_range(row, column + 3, row, column + 6,
                              record['name'], txt_border)
            sheet.merge_range(row, column + 7, row, column + 8,
                              record['invoice_date_due'], txt_border)
            sheet.merge_range(row, column + 9, row, column + 11,
                              sub_total, txt_border)
            sheet.merge_range(row, column + 12, row, column + 14,
                              amount_due, txt_border)
            sheet.merge_range(row, column + 15, row, column + 17,
                              balance, txt_border)
            row = row + 1
        sheet.write(row + 2, column + 1, 'Total Amount: ', cell_format)
        sheet.merge_range(row + 2, column + 3, row + 2, column + 4,
                          total, txt)
        sheet.write(row + 4, column + 1, 'Balance Due: ', cell_format)
        sheet.merge_range(row + 4, column + 3, row + 4, column + 4,
                          remain_balance, txt)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def action_share_xlsx(self):
        """ Action for sharing xlsx report via email"""
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet()
            cell_format = workbook.add_format({
                'font_size': '14px', 'bold': True})
            txt = workbook.add_format({'font_size': '13px'})
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '22px'})
            sheet.merge_range('B2:P4', 'Payment Statement Report', head)
            date_style = workbook.add_format(
                {'text_wrap': True, 'align': 'center',
                 'num_format': 'yyyy-mm-dd'})

            if data['customer']:
                sheet.write('B7:C7', 'Customer : ', cell_format)
                sheet.merge_range('D7:G7', data['customer'], txt)
            sheet.write('B9:C7', 'Address : ', cell_format)
            if data['street']:
                sheet.merge_range('D9:F9', data['street'], txt)
            if data['street2']:
                sheet.merge_range('D10:F10', data['street2'], txt)
            if data['city']:
                sheet.merge_range('D11:F11', data['city'], txt)
            if data['state']:
                sheet.merge_range('D12:F12', data['state'], txt)
            if data['zip']:
                sheet.merge_range('D13:F13', data['zip'], txt)
            sheet.write('B15', 'Date', cell_format)
            sheet.write('D15', 'Invoice/Bill Number', cell_format)
            sheet.write('H15', 'Due Date', cell_format)
            sheet.write('J15', 'Invoices/Debit', cell_format)
            sheet.write('M15', 'Amount Due', cell_format)
            sheet.write('P15', 'Balance Due', cell_format)
            row = 16
            column = 0
            for record in data['my_data']:
                sub_total = data['currency'] + str(record['sub_total'])
                amount_due = data['currency'] + str(record['amount_due'])
                balance = data['currency'] + str(record['balance'])
                total = data['currency'] + str(data['total'])
                remain_balance = data['currency'] + str(data['balance'])

                sheet.merge_range(row, column + 1, row, column + 2,
                                  record['invoice_date'], date_style)
                sheet.merge_range(row, column + 3, row, column + 5,
                                  record['name'], txt)
                sheet.merge_range(row, column + 7, row, column + 8,
                                  record['invoice_date_due'], date_style)
                sheet.merge_range(row, column + 9, row, column + 10,
                                  sub_total, txt)
                sheet.merge_range(row, column + 12, row, column + 13,
                                  amount_due, txt)
                sheet.merge_range(row, column + 15, row, column + 16,
                                  balance, txt)
                row = row + 1
            sheet.write(row + 2, column + 1, 'Total Amount : ', cell_format)
            sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                              total, txt)
            sheet.write(row + 4, column + 1, 'Balance Due : ', cell_format)
            sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                              remain_balance, txt)
            workbook.close()
            output.seek(0)
            xlsx = base64.b64encode(output.read())
            output.close()
            ir_values = {
                'name': "Statement Report.xlsx",
                'type': 'binary',
                'datas': xlsx,
                'store_fname': xlsx,
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached your'
                             ' payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    def auto_week_statement_report(self):
        """ Action for sending automatic weekly statement
            of both pdf and xlsx report """

        partner = []
        invoice = self.env['account.move'].search(
            [('move_type', 'in', ['out_invoice', 'in_invoice']),
             ('payment_state', '!=', 'paid'),
             ('state', '=', 'posted')])

        for inv in invoice:
            if inv.partner_id not in partner:
                partner.append(inv.partner_id)

        for rec in partner:
            if rec.id:
                main_query = """ SELECT name , invoice_date, invoice_date_due,
                            amount_total_signed AS sub_total,
                            amount_residual_signed AS amount_due ,
                            amount_residual AS balance
                    FROM account_move WHERE move_type
                        IN ('out_invoice', 'in_invoice')
                       AND state ='posted' AND payment_state != 'paid'
                       AND company_id = '%s' AND partner_id = '%s'
                    GROUP BY name, invoice_date, invoice_date_due,
                    amount_total_signed, amount_residual_signed,
                    amount_residual
                    ORDER by name DESC""" % (self.env.company.id, rec.id)

                self.env.cr.execute(main_query)
                main = self.env.cr.dictfetchall()
                data = {
                    'customer': rec.display_name,
                    'street': rec.street,
                    'street2': rec.street2,
                    'city': rec.city,
                    'state': rec.state_id.name,
                    'zip': rec.zip,
                    'my_data': main,
                }
                report = self.env['ir.actions.report']._render_qweb_pdf(
                    'statement_report.res_partner_action',
                    self, data=data)
                data_record = base64.b64encode(report[0])
                ir_values = {
                    'name': 'Statement Report',
                    'type': 'binary',
                    'datas': data_record,
                    'mimetype': 'application/pdf',
                    'res_model': 'res.partner',
                }
                attachment1 = self.env[
                    'ir.attachment'].sudo().create(ir_values)
                # FOR XLSX
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                sheet = workbook.add_worksheet()
                cell_format = workbook.add_format(
                    {'font_size': '14px', 'bold': True})
                txt = workbook.add_format({'font_size': '13px'})
                head = workbook.add_format(
                    {'align': 'center', 'bold': True, 'font_size': '22px'})
                sheet.merge_range('B2:P4', 'Payment Statement Report', head)
                date_style = workbook.add_format(
                    {'text_wrap': True, 'align': 'center',
                     'num_format': 'yyyy-mm-dd'})

                if data['customer']:
                    sheet.write('B7:D7', 'Customer/Supplier : ', cell_format)
                    sheet.merge_range('E7:H7', data['customer'], txt)
                sheet.write('B9:C7', 'Address : ', cell_format)
                if data['street']:
                    sheet.merge_range('D9:F9', data['street'], txt)
                if data['street2']:
                    sheet.merge_range('D10:F10', data['street2'], txt)
                if data['city']:
                    sheet.merge_range('D11:F11', data['city'], txt)
                if data['state']:
                    sheet.merge_range('D12:F12', data['state'], txt)
                if data['zip']:
                    sheet.merge_range('D13:F13', data['zip'], txt)

                sheet.write('B15', 'Date', cell_format)
                sheet.write('D15', 'Invoice/Bill Number', cell_format)
                sheet.write('H15', 'Due Date', cell_format)
                sheet.write('J15', 'Invoices/Debit', cell_format)
                sheet.write('M15', 'Amount Due', cell_format)
                sheet.write('P15', 'Balance Due', cell_format)

                row = 16
                column = 0

                for record in data['my_data']:
                    sheet.merge_range(row, column + 1, row, column + 2,
                                      record['invoice_date'], date_style)
                    sheet.merge_range(row, column + 3, row, column + 5,
                                      record['name'], txt)
                    sheet.merge_range(row, column + 7, row, column + 8,
                                      record['invoice_date_due'], date_style)
                    sheet.merge_range(row, column + 9, row, column + 10,
                                      record['sub_total'], txt)
                    sheet.merge_range(row, column + 12, row, column + 13,
                                      record['amount_due'], txt)
                    sheet.merge_range(row, column + 15, row, column + 16,
                                      record['balance'], txt)
                    row = row + 1
                workbook.close()
                output.seek(0)
                xlsx = base64.b64encode(output.read())
                output.close()
                ir_values = {
                    'name': "Statement Report.xlsx",
                    'type': 'binary',
                    'datas': xlsx,
                    'store_fname': xlsx,
                }
                attachment2 = self.env['ir.attachment'].sudo().create(
                    ir_values)
                email_values = {
                    'email_to': rec.email,
                    'subject': 'Weekly Payment Statement Report',
                    'body_html': '<p>Dear <strong> Mr/Miss. ' + rec.name +
                                 '</strong> </p> <p> We have attached your '
                                 'payment statement. Please check </p> <p>'
                                 'Best regards, </p><p> ' + self.env.user.name,
                    'attachment_ids': [attachment1.id, attachment2.id]
                }
                mail = self.env['mail.mail'].sudo().create(email_values)
                mail.send()

    def auto_month_statement_report(self):
        """ Action for sending automatic monthly statement report
            of both pdf and xlsx report"""

        partner = []
        invoice = self.env['account.move'].search(
            [('move_type', 'in', ['out_invoice', 'in_invoice']),
             ('payment_state', '!=', 'paid'),
             ('state', '=', 'posted')])

        for inv in invoice:
            if inv.partner_id not in partner:
                partner.append(inv.partner_id)

        for rec in partner:
            if rec.id:
                main_query = """SELECT name , invoice_date, invoice_date_due,
                        amount_total_signed AS sub_total,
                        amount_residual_signed AS amount_due ,
                        amount_residual AS balance
                   FROM account_move WHERE move_type
                        IN ('out_invoice', 'in_invoice')
                        AND state ='posted'
                        AND payment_state != 'paid'
                        AND company_id = '%s' AND partner_id = '%s'
                   GROUP BY name, invoice_date, invoice_date_due,
                    amount_total_signed, amount_residual_signed,
                    amount_residual
                    ORDER by name DESC""" % (self.env.company.id, rec.id)

                self.env.cr.execute(main_query)
                main = self.env.cr.dictfetchall()
                data = {
                    'customer': rec.display_name,
                    'street': rec.street,
                    'street2': rec.street2,
                    'city': rec.city,
                    'state': rec.state_id.name,
                    'zip': rec.zip,
                    'my_data': main,
                }
                report = self.env['ir.actions.report']._render_qweb_pdf(
                    'statement_report.res_partner_action',
                    self, data=data)
                data_record = base64.b64encode(report[0])
                ir_values = {
                    'name': 'Statement Report',
                    'type': 'binary',
                    'datas': data_record,
                    'mimetype': 'application/pdf',
                    'res_model': 'res.partner',
                }
                attachment1 = self.env['ir.attachment'].sudo().create(
                    ir_values)
                # FOR XLSX
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                sheet = workbook.add_worksheet()
                cell_format = workbook.add_format(
                    {'font_size': '14px', 'bold': True})
                txt = workbook.add_format({'font_size': '13px'})
                head = workbook.add_format(
                    {'align': 'center', 'bold': True, 'font_size': '22px'})
                sheet.merge_range('B2:P4', 'Payment Statement Report', head)
                date_style = workbook.add_format(
                    {'text_wrap': True, 'align': 'center',
                     'num_format': 'yyyy-mm-dd'})

                if data['customer']:
                    sheet.write('B7:D7', 'Customer/Supplier : ', cell_format)
                    sheet.merge_range('E7:H7', data['customer'], txt)
                sheet.write('B9:C7', 'Address : ', cell_format)
                if data['street']:
                    sheet.merge_range('D9:F9', data['street'], txt)
                if data['street2']:
                    sheet.merge_range('D10:F10', data['street2'], txt)
                if data['city']:
                    sheet.merge_range('D11:F11', data['city'], txt)
                if data['state']:
                    sheet.merge_range('D12:F12', data['state'], txt)
                if data['zip']:
                    sheet.merge_range('D13:F13', data['zip'], txt)

                sheet.write('B15', 'Date', cell_format)
                sheet.write('D15', 'Invoice/Bill Number', cell_format)
                sheet.write('H15', 'Due Date', cell_format)
                sheet.write('J15', 'Invoices/Debit', cell_format)
                sheet.write('M15', 'Amount Due', cell_format)
                sheet.write('P15', 'Balance Due', cell_format)

                row = 16
                column = 0

                for record in data['my_data']:
                    sheet.merge_range(row, column + 1, row, column + 2,
                                      record['invoice_date'], date_style)
                    sheet.merge_range(row, column + 3, row, column + 5,
                                      record['name'], txt)
                    sheet.merge_range(row, column + 7, row, column + 8,
                                      record['invoice_date_due'], date_style)
                    sheet.merge_range(row, column + 9, row, column + 10,
                                      record['sub_total'], txt)
                    sheet.merge_range(row, column + 12, row, column + 13,
                                      record['amount_due'], txt)
                    sheet.merge_range(row, column + 15, row, column + 16,
                                      record['balance'], txt)
                    row = row + 1
                workbook.close()
                output.seek(0)
                xlsx = base64.b64encode(output.read())
                output.close()
                ir_values = {
                    'name': "Statement Report.xlsx",
                    'type': 'binary',
                    'datas': xlsx,
                    'store_fname': xlsx,
                }
                attachment2 = self.env['ir.attachment'].sudo().create(
                    ir_values)
                email_values = {
                    'email_to': rec.email,
                    'subject': 'Monthly Payment Statement Report',
                    'body_html': '<p>Dear <strong> Mr/Miss. ' + rec.name +
                                 '</strong> </p> <p> We have attached your '
                                 'payment statement. '
                                 'Please check </p> <p>Best regards,'
                                 ' </p> <p>' + self.env.user.name,
                    'attachment_ids': [attachment1.id, attachment2.id]
                }
                mail = self.env['mail.mail'].sudo().create(email_values)
                mail.send()

    def action_vendor_print_pdf(self):
        """ Action for printing vendor pdf report """
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('in_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('in_invoice')"""

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return self.env.ref(
                'statement_report.res_partner_action').report_action(
                self, data=data)
        else:
            raise ValidationError('There is no statement to print')

    def action_vendor_share_pdf(self):
        """ Action for sharing pdf report of vendor via email """
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('in_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('in_invoice')"""

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            report = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'statement_report.res_partner_action', self, data=data)
            data_record = base64.b64encode(report[0])
            ir_values = {
                'name': 'Statement Report',
                'type': 'binary',
                'datas': data_record,
                'mimetype': 'application/pdf',
                'res_model': 'res.partner'
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)

            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached'
                             ' your payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    def action_vendor_print_xlsx(self):
        """ Action for printing xlsx report of vendor """
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('in_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('in_invoice')"""

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()

            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return {
                'type': 'ir.actions.report',
                'data': {
                    'model': 'res.partner',
                    'options': json.dumps(data,
                                          default=date_utils.json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Payment Statement Report'
                },
                'report_type': 'xlsx',
            }
        else:
            raise ValidationError('There is no statement to print')

    def action_vendor_share_xlsx(self):
        """ Action for sharing vendor xlsx report via email """
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('in_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('in_invoice')"""

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet()
            cell_format = workbook.add_format({
                'font_size': '14px', 'bold': True})
            txt = workbook.add_format({'font_size': '13px'})
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '22px'})
            sheet.merge_range('B2:P4', 'Payment Statement Report', head)
            date_style = workbook.add_format({
                'text_wrap': True, 'align': 'center',
                'num_format': 'yyyy-mm-dd'})
            if data['customer']:
                sheet.write('B7:C7', 'Supplier : ', cell_format)
                sheet.merge_range('D7:G7', data['customer'], txt)
            sheet.write('B9:C7', 'Address : ', cell_format)
            if data['street']:
                sheet.merge_range('D9:F9', data['street'], txt)
            if data['street2']:
                sheet.merge_range('D10:F10', data['street2'], txt)
            if data['city']:
                sheet.merge_range('D11:F11', data['city'], txt)
            if data['state']:
                sheet.merge_range('D12:F12', data['state'], txt)
            if data['zip']:
                sheet.merge_range('D13:F13', data['zip'], txt)
            sheet.write('B15', 'Date', cell_format)
            sheet.write('D15', 'Invoice/Bill Number', cell_format)
            sheet.write('H15', 'Due Date', cell_format)
            sheet.write('J15', 'Invoices/Debit', cell_format)
            sheet.write('M15', 'Amount Due', cell_format)
            sheet.write('P15', 'Balance Due', cell_format)

            row = 16
            column = 0
            for record in data['my_data']:
                sub_total = data['currency'] + str(record['sub_total'])
                amount_due = data['currency'] + str(record['amount_due'])
                balance = data['currency'] + str(record['balance'])
                total = data['currency'] + str(data['total'])
                remain_balance = data['currency'] + str(data['balance'])

                sheet.merge_range(row, column + 1, row, column + 2,
                                  record['invoice_date'], date_style)
                sheet.merge_range(row, column + 3, row, column + 5,
                                  record['name'], txt)
                sheet.merge_range(row, column + 7, row, column + 8,
                                  record['invoice_date_due'], date_style)
                sheet.merge_range(row, column + 9, row, column + 10,
                                  sub_total, txt)
                sheet.merge_range(row, column + 12, row, column + 13,
                                  amount_due, txt)
                sheet.merge_range(row, column + 15, row, column + 16,
                                  balance, txt)
                row = row + 1

            sheet.write(row + 2, column + 1, 'Total Amount : ', cell_format)
            sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                              total, txt)
            sheet.write(row + 4, column + 1, 'Balance Due : ', cell_format)
            sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                              remain_balance, txt)

            workbook.close()
            output.seek(0)
            xlsx = base64.b64encode(output.read())
            output.close()
            ir_values = {
                'name': "Statement Report",
                'type': 'binary',
                'datas': xlsx,
                'store_fname': xlsx,
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)

            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached your '
                             'payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')
