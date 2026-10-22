# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import io
import json
import xlsxwriter
from markupsafe import Markup
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL
from odoo.tools.json import json_default


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

    def _compute_customer_report_ids(self):
        """ For computing 'invoices' of partner """
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
        """ Return select query """
        return SQL(
            """SELECT name , invoice_date, invoice_date_due,
                    amount_total_signed AS sub_total,
                    amount_residual_signed AS amount_due ,
                    amount_residual AS balance
            FROM account_move WHERE payment_state != 'paid'
            AND state ='posted' AND partner_id = %s
            AND company_id = %s""", self.id, self.env.company.id)

    def amount_query(self, partner_id=False):
        """ Return query for calculating total amount """
        return SQL(
            """SELECT SUM(amount_total_signed) AS total,
                    SUM(amount_residual) AS balance
                FROM account_move WHERE payment_state != 'paid'
                AND state ='posted' AND partner_id = %s
                AND company_id = %s""",
            self.id if self else partner_id, self.env.company.id)

    def _statement_mail_body(self):
        """ Return the escaped body of the statement email """
        return Markup(
            '<p>%s <strong>%s</strong></p><p>%s</p><p>%s</p><p>%s</p>'
        ) % (self.env._('Dear'), self.name,
             self.env._('We have attached your payment statement. '
                        'Please check.'),
             self.env._('Best regards,'), self.env.user.name)

    def action_share_pdf(self):
        """ Action for sharing customer pdf report """
        self.ensure_one()
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query = SQL("%s AND move_type IN ('out_invoice')", main_query)
            amount = self.amount_query()
            amount = SQL("%s AND move_type IN ('out_invoice')", amount)
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
            ir_values = {
                'name': 'Statement Report',
                'type': 'binary',
                'raw': report[0],
                'mimetype': 'application/pdf',
                'res_model': 'res.partner'
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': self.env._('Payment Statement Report'),
                'body_html': self._statement_mail_body(),
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': self.env._('Email sent successfully'),
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError(
                self.env._('There is no statement to send'))

    def action_print_pdf(self):
        """ Action for printing pdf report """
        self.ensure_one()
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query = SQL("%s AND move_type IN ('out_invoice')", main_query)
            amount = self.amount_query()
            amount = SQL("%s AND move_type IN ('out_invoice')", amount)
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
            raise ValidationError(
                self.env._('There is no statement to print'))

    def action_print_xlsx(self):
        """ Action for printing xlsx report of customers """
        self.ensure_one()
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query = SQL("%s AND move_type IN ('out_invoice')", main_query)
            amount = self.amount_query()
            amount = SQL("%s AND move_type IN ('out_invoice')", amount)
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
                                          default=json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Payment Statement Report'
                },
                'report_type': 'xlsx',
            }
        else:
            raise ValidationError(
                self.env._('There is no statement to print'))

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
        sheet.merge_range('B2:Q4', self.env._('Payment Statement Report'), head)
        if data['customer']:
            sheet.merge_range('B7:D7', self.env._('Customer/Supplier: '), cell_format)
            sheet.merge_range('E7:H7', data['customer'], txt)
        sheet.merge_range('B9:C9', self.env._('Address: '), cell_format)
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
        sheet.merge_range('B15:C15', self.env._('Date'), cell_format_with_color)
        sheet.merge_range('D15:G15', self.env._('Invoice/Bill Number'),
                          cell_format_with_color)
        sheet.merge_range('H15:I15', self.env._('Due Date'), cell_format_with_color)
        sheet.merge_range('J15:L15', self.env._('Invoices/Debit'), cell_format_with_color)
        sheet.merge_range('M15:O15', self.env._('Amount Due'), cell_format_with_color)
        sheet.merge_range('P15:R15', self.env._('Balance Due'), cell_format_with_color)
        row = 15
        column = 0
        total = data['currency'] + str(data['total'])
        remain_balance = data['currency'] + str(data['balance'])
        for record in data['my_data']:
            sub_total = data['currency'] + str(record['sub_total'])
            amount_due = data['currency'] + str(record['amount_due'])
            balance = data['currency'] + str(record['balance'])
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
        sheet.write(row + 2, column + 1, self.env._('Total Amount: '), cell_format)
        sheet.merge_range(row + 2, column + 3, row + 2, column + 4,
                          total, txt)
        sheet.write(row + 4, column + 1, self.env._('Balance Due: '), cell_format)
        sheet.merge_range(row + 4, column + 3, row + 4, column + 4,
                          remain_balance, txt)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def action_share_xlsx(self):
        """ Action for sharing xlsx report via email """
        self.ensure_one()
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query = SQL("%s AND move_type IN ('out_invoice')", main_query)
            amount = self.amount_query()
            amount = SQL("%s AND move_type IN ('out_invoice')", amount)
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
            sheet.merge_range('B2:P4', self.env._('Payment Statement Report'), head)
            date_style = workbook.add_format(
                {'text_wrap': True, 'align': 'center',
                 'num_format': 'yyyy-mm-dd'})
            if data['customer']:
                sheet.write('B7', self.env._('Customer: '), cell_format)
                sheet.merge_range('D7:G7', data['customer'], txt)
            sheet.write('B9', self.env._('Address: '), cell_format)
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
            sheet.write('B15', self.env._('Date'), cell_format)
            sheet.write('D15', self.env._('Invoice/Bill Number'), cell_format)
            sheet.write('H15', self.env._('Due Date'), cell_format)
            sheet.write('J15', self.env._('Invoices/Debit'), cell_format)
            sheet.write('M15', self.env._('Amount Due'), cell_format)
            sheet.write('P15', self.env._('Balance Due'), cell_format)
            row = 16
            column = 0
            total = data['currency'] + str(data['total'])
            remain_balance = data['currency'] + str(data['balance'])
            for record in data['my_data']:
                sub_total = data['currency'] + str(record['sub_total'])
                amount_due = data['currency'] + str(record['amount_due'])
                balance = data['currency'] + str(record['balance'])
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
            sheet.write(row + 2, column + 1, self.env._('Total Amount: '), cell_format)
            sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                              total, txt)
            sheet.write(row + 4, column + 1, self.env._('Balance Due: '), cell_format)
            sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                              remain_balance, txt)
            workbook.close()
            output.seek(0)
            xlsx = output.read()
            output.close()
            ir_values = {
                'name': "Statement Report.xlsx",
                'type': 'binary',
                'raw': xlsx,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': self.env._('Payment Statement Report'),
                'body_html': self._statement_mail_body(),
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': self.env._('Email sent successfully'),
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError(
                self.env._('There is no statement to send'))

    def auto_week_statement_report(self):
        """ Run the automatic statement for every company """
        for company in self.env['res.company'].sudo().search(
                [('active', '=', True)]):
            self.sudo().with_company(company)._auto_week_statement_report()

    def _auto_week_statement_report(self):
        """ Action for sending automatic weekly statement
            of both pdf and xlsx report """
        partner = set()
        invoice = self.env['account.move'].search(
            [('move_type', 'in', ['out_invoice', 'in_invoice']),
             ('payment_state', '!=', 'paid'),
             ('state', '=', 'posted'),
             ('company_id', '=', self.env.company.id)])
        for inv in invoice:
            if inv.partner_id not in partner:
                partner.add(inv.partner_id)
        for rec in partner:
            if rec.id:
                main_query = """ SELECT name , invoice_date, invoice_date_due,
                            amount_total_signed AS sub_total,
                            amount_residual_signed AS amount_due ,
                            amount_residual AS balance
                    FROM account_move WHERE move_type
                        IN ('out_invoice', 'in_invoice')
                       AND state ='posted' AND payment_state != 'paid'
                       AND company_id = %s AND partner_id = %s
                    GROUP BY name, invoice_date, invoice_date_due,
                    amount_total_signed, amount_residual_signed,
                    amount_residual
                    ORDER by name DESC"""

                amount = self.amount_query(partner_id=rec.id)
                amount = SQL(
                    "%s AND move_type IN ('out_invoice', 'in_invoice')",
                    amount)
                self.env.cr.execute(amount)
                amount = self.env.cr.dictfetchall()
                self.env.cr.execute(
                    main_query, (self.env.company.id, rec.id))
                main = self.env.cr.dictfetchall()
                data = {
                    'customer': rec.display_name,
                    'street': rec.street,
                    'street2': rec.street2,
                    'city': rec.city,
                    'state': rec.state_id.name,
                    'zip': rec.zip,
                    'my_data': main,
                    'total': amount[0]['total'],
                    'balance': amount[0]['balance'],
                    'currency': rec.currency_id.symbol,
                }
                report = self.env['ir.actions.report']._render_qweb_pdf(
                    'statement_report.res_partner_action',
                    self, data=data)
                ir_values = {
                    'name': 'Statement Report',
                    'type': 'binary',
                    'raw': report[0],
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
                sheet.merge_range('B2:P4', self.env._('Payment Statement Report'), head)
                date_style = workbook.add_format(
                    {'text_wrap': True, 'align': 'center',
                     'num_format': 'yyyy-mm-dd'})
                if data['customer']:
                    sheet.write('B7', self.env._('Customer/Supplier: '), cell_format)
                    sheet.merge_range('E7:H7', data['customer'], txt)
                sheet.write('B9', self.env._('Address: '), cell_format)
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

                sheet.write('B15', self.env._('Date'), cell_format)
                sheet.write('D15', self.env._('Invoice/Bill Number'), cell_format)
                sheet.write('H15', self.env._('Due Date'), cell_format)
                sheet.write('J15', self.env._('Invoices/Debit'), cell_format)
                sheet.write('M15', self.env._('Amount Due'), cell_format)
                sheet.write('P15', self.env._('Balance Due'), cell_format)

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
                total = data['currency'] + str(data['total'])
                remain_balance = data['currency'] + str(data['balance'])
                sheet.write(row + 2, column + 1, self.env._('Total Amount: '), cell_format)
                sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                                  total, txt)
                sheet.write(row + 4, column + 1, self.env._('Balance Due: '), cell_format)
                sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                                  remain_balance, txt)
                workbook.close()
                output.seek(0)
                xlsx = output.read()
                output.close()
                ir_values = {
                    'name': "Statement Report.xlsx",
                    'type': 'binary',
                    'raw': xlsx,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                }
                attachment2 = self.env['ir.attachment'].sudo().create(
                    ir_values)
                email_values = {
                    'email_to': rec.email,
                    'subject': self.env._('Weekly Payment Statement Report'),
                    'body_html': rec._statement_mail_body(),
                    'attachment_ids': [attachment1.id, attachment2.id]
                }
                mail = self.env['mail.mail'].sudo().create(email_values)
                mail.send()

    def auto_month_statement_report(self):
        """ Run the automatic statement for every company """
        for company in self.env['res.company'].sudo().search(
                [('active', '=', True)]):
            self.sudo().with_company(company)._auto_month_statement_report()

    def _auto_month_statement_report(self):
        """ Action for sending automatic monthly statement report
            of both pdf and xlsx. """
        partner = set()
        invoice = self.env['account.move'].search(
            [('move_type', 'in', ['out_invoice', 'in_invoice']),
             ('payment_state', '!=', 'paid'),
             ('state', '=', 'posted'),
             ('company_id', '=', self.env.company.id)])
        for inv in invoice:
            if inv.partner_id not in partner:
                partner.add(inv.partner_id)
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
                        AND company_id = %s AND partner_id = %s
                   GROUP BY name, invoice_date, invoice_date_due,
                    amount_total_signed, amount_residual_signed,
                    amount_residual
                    ORDER by name DESC"""

                self.env.cr.execute(
                    main_query, (self.env.company.id, rec.id))
                main = self.env.cr.dictfetchall()
                amount = self.amount_query(partner_id=rec.id)
                amount = SQL(
                    "%s AND move_type IN ('out_invoice', 'in_invoice')",
                    amount)
                self.env.cr.execute(amount)
                amount = self.env.cr.dictfetchall()
                data = {
                    'customer': rec.display_name,
                    'street': rec.street,
                    'street2': rec.street2,
                    'city': rec.city,
                    'state': rec.state_id.name,
                    'zip': rec.zip,
                    'my_data': main,
                    'total': amount[0]['total'],
                    'balance': amount[0]['balance'],
                    'currency': rec.currency_id.symbol,
                }
                report = self.env['ir.actions.report']._render_qweb_pdf(
                    'statement_report.res_partner_action',
                    self, data=data)
                ir_values = {
                    'name': 'Statement Report',
                    'type': 'binary',
                    'raw': report[0],
                    'mimetype': 'application/pdf',
                    'res_model': 'res.partner',
                }
                attachment1 = self.env['ir.attachment'].sudo().create(ir_values)
                # FOR XLSX
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                sheet = workbook.add_worksheet()
                cell_format = workbook.add_format(
                    {'font_size': '14px', 'bold': True})
                txt = workbook.add_format({'font_size': '13px'})
                head = workbook.add_format(
                    {'align': 'center', 'bold': True, 'font_size': '22px'})
                sheet.merge_range('B2:P4', self.env._('Payment Statement Report'), head)
                date_style = workbook.add_format(
                    {'text_wrap': True, 'align': 'center',
                     'num_format': 'yyyy-mm-dd'})
                if data['customer']:
                    sheet.write('B7', self.env._('Customer/Supplier: '), cell_format)
                    sheet.merge_range('E7:H7', data['customer'], txt)
                sheet.write('B9', self.env._('Address: '), cell_format)
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

                sheet.write('B15', self.env._('Date'), cell_format)
                sheet.write('D15', self.env._('Invoice/Bill Number'), cell_format)
                sheet.write('H15', self.env._('Due Date'), cell_format)
                sheet.write('J15', self.env._('Invoices/Debit'), cell_format)
                sheet.write('M15', self.env._('Amount Due'), cell_format)
                sheet.write('P15', self.env._('Balance Due'), cell_format)
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
                total = data['currency'] + str(data['total'])
                remain_balance = data['currency'] + str(data['balance'])
                sheet.write(row + 2, column + 1, self.env._('Total Amount: '), cell_format)
                sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                                  total, txt)
                sheet.write(row + 4, column + 1, self.env._('Balance Due: '), cell_format)
                sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                                  remain_balance, txt)
                workbook.close()
                output.seek(0)
                xlsx = output.read()
                output.close()
                ir_values = {
                    'name': "Statement Report.xlsx",
                    'type': 'binary',
                    'raw': xlsx,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                }
                attachment2 = self.env['ir.attachment'].sudo().create(
                    ir_values)
                email_values = {
                    'email_to': rec.email,
                    'subject': self.env._('Monthly Payment Statement Report'),
                    'body_html': rec._statement_mail_body(),
                    'attachment_ids': [attachment1.id, attachment2.id]
                }
                mail = self.env['mail.mail'].sudo().create(email_values)
                mail.send()

    def action_vendor_print_pdf(self):
        """ Action for printing vendor pdf report """
        self.ensure_one()
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query = SQL("%s AND move_type IN ('in_invoice')", main_query)
            amount = self.amount_query()
            amount = SQL("%s AND move_type IN ('in_invoice')", amount)

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
            raise ValidationError(
                self.env._('There is no statement to print'))

    def action_vendor_share_pdf(self):
        """ Action for sharing pdf report of vendor via email """
        self.ensure_one()
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query = SQL("%s AND move_type IN ('in_invoice')", main_query)
            amount = self.amount_query()
            amount = SQL("%s AND move_type IN ('in_invoice')", amount)

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
            ir_values = {
                'name': 'Statement Report',
                'type': 'binary',
                'raw': report[0],
                'mimetype': 'application/pdf',
                'res_model': 'res.partner'
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)

            email_values = {
                'email_to': self.email,
                'subject': self.env._('Payment Statement Report'),
                'body_html': self._statement_mail_body(),
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': self.env._('Email sent successfully'),
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError(
                self.env._('There is no statement to send'))

    def action_vendor_print_xlsx(self):
        """ Action for printing xlsx report of vendor """
        self.ensure_one()
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query = SQL("%s AND move_type IN ('in_invoice')", main_query)
            amount = self.amount_query()
            amount = SQL("%s AND move_type IN ('in_invoice')", amount)

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
                                          default=json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Payment Statement Report'
                },
                'report_type': 'xlsx',
            }
        else:
            raise ValidationError(
                self.env._('There is no statement to print'))

    def action_vendor_share_xlsx(self):
        """ Action for sharing vendor xlsx report via email """
        self.ensure_one()
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query = SQL("%s AND move_type IN ('in_invoice')", main_query)
            amount = self.amount_query()
            amount = SQL("%s AND move_type IN ('in_invoice')", amount)

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
            sheet.merge_range('B2:P4', self.env._('Payment Statement Report'), head)
            date_style = workbook.add_format({
                'text_wrap': True, 'align': 'center',
                'num_format': 'yyyy-mm-dd'})
            if data['customer']:
                sheet.write('B7', self.env._('Supplier: '), cell_format)
                sheet.merge_range('D7:G7', data['customer'], txt)
            sheet.write('B9', self.env._('Address: '), cell_format)
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
            sheet.write('B15', self.env._('Date'), cell_format)
            sheet.write('D15', self.env._('Invoice/Bill Number'), cell_format)
            sheet.write('H15', self.env._('Due Date'), cell_format)
            sheet.write('J15', self.env._('Invoices/Debit'), cell_format)
            sheet.write('M15', self.env._('Amount Due'), cell_format)
            sheet.write('P15', self.env._('Balance Due'), cell_format)

            row = 16
            column = 0
            total = data['currency'] + str(data['total'])
            remain_balance = data['currency'] + str(data['balance'])
            for record in data['my_data']:
                sub_total = data['currency'] + str(record['sub_total'])
                amount_due = data['currency'] + str(record['amount_due'])
                balance = data['currency'] + str(record['balance'])

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

            sheet.write(row + 2, column + 1, self.env._('Total Amount: '), cell_format)
            sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                              total, txt)
            sheet.write(row + 4, column + 1, self.env._('Balance Due: '), cell_format)
            sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                              remain_balance, txt)

            workbook.close()
            output.seek(0)
            xlsx = output.read()
            output.close()
            ir_values = {
                'name': "Statement Report",
                'type': 'binary',
                'raw': xlsx,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': self.env._('Payment Statement Report'),
                'body_html': self._statement_mail_body(),
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': self.env._('Email sent successfully'),
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError(
                self.env._('There is no statement to send'))
