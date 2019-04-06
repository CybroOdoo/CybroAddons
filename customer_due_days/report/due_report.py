# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, models,fields, _


class CustomerDueReportXLSX(models.AbstractModel):
    _name = 'report.customer_due_days.report_customer_due_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook,  data, vals):
        sheet = workbook.add_worksheet('Customer Due Report')
        format1 = workbook.add_format({'font_size': 15, 'align': 'center', 'bg_color': '#8a98a8', 'bold': True})
        format2 = workbook.add_format(
            {'align': 'center', 'font_size': 10, 'bg_color': '#8a98a8', 'bottom': 1, 'bold': True})
        format3 = workbook.add_format({'align': 'left', 'font_size': 10, 'bg_color': '#a7b2be', 'bottom': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'bg_color': '#a7b2be', 'align': 'left', 'bottom': 1})
        format5 = workbook.add_format(
            {'font_size': 10, 'bg_color': '#a7b2be', 'align': 'right', 'bottom': 1, 'bold': True})
        format6 = workbook.add_format({'align': 'left', 'font_size': 10, 'bg_color': '#c4ccd4', 'bottom': 1})
        format7 = workbook.add_format({'align': 'right', 'font_size': 10, 'bg_color': '#c4ccd4', 'bottom': 1})
        format8= workbook.add_format({'align': 'right', 'font_size': 10, 'bg_color': '#c4ccd4', 'bottom': 1, 'bold': True})
        date_time_default_col1_style = workbook.add_format(
            {'align': 'left', 'font_size': 10, 'bg_color': '#a7b2be', 'num_format': 'dd/mm/yy', 'bottom': 1})
        date_time_default_col1_style_2 = workbook.add_format(
            {'align': 'left', 'font_size': 10, 'bg_color': '#c4ccd4', 'num_format': 'dd/mm/yy', 'bottom': 1})
        format10 = workbook.add_format({'align': 'right', 'font_size': 10})
        sheet.set_row(0, 30)
        report_date = datetime.now().strftime("%Y-%m-%d")
        sheet.merge_range('A1:H1', 'CUSTOMER DUE REPORT', format1)
        sheet.write('A3', 'Report Date', format2)
        sheet.write('A4', report_date, format10)
        sheet.write('A6', 'PARTNER', format2)
        sheet.write('B6', 'EMAIL', format2)
        sheet.write('C6', 'PHONE', format2)
        sheet.write('D6', 'REFERENCE', format2)
        sheet.write('E6', 'DUE DATE', format2)
        sheet.write('F6', 'DUE DAYS', format2)
        sheet.write('G6', 'DUE AMOUNT', format2)
        sheet.write('H6', 'TOTAL DUE', format2)
        row_num = 6
        col_num = 0
        cr = self._cr
        for record in self.env['res.partner'].search([('customer', '=', True)]):
            total_overdue = 0
            today = fields.Date.today()
            cr.execute("""SELECT account_move_line.date_maturity as date_maturity,account_move_line.company_id as company_id, 
                          SUM(account_move_line.amount_residual) as amount_residual,
                          account_move_line.date as date,am.ref as invoice,am.name as entry
                         FROM account_move_line
                         LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
                         LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                         LEFT JOIN account_move am ON (am.id=account_move_line.move_id)
                         WHERE (account_move_line.date_maturity < %s) AND 
                         act.type = 'receivable'
                         AND account_move_line.partner_id = %s
                         AND account_move_line.reconciled IS FALSE AND a.deprecated IS FALSE 
                         GROUP BY account_move_line.date_maturity,account_move_line.company_id,account_move_line.amount_residual,
                         account_move_line.date,am.ref,am.name
                         """, (today, record.id))
            unreconciled_aml_ids = cr.dictfetchall()
            if unreconciled_aml_ids:
                row_old = row_num
                if len(unreconciled_aml_ids) > 1:
                    sheet.write(row_num, col_num, record.name, format3)
                    sheet.write(row_num, col_num + 1, '', format3)
                    sheet.write(row_num, col_num + 2, '', format3)
                    sheet.write(row_num, col_num + 3, '', format3)
                    sheet.write(row_num, col_num + 4, '', format3)
                    sheet.write(row_num, col_num + 5, '', format3)
                    sheet.write(row_num, col_num + 6, '', format3)
                    row_num += 1
                    for aml in unreconciled_aml_ids:
                        if aml['company_id'] == self.env.user.company_id.id:
                            amount = aml['amount_residual']
                            total_overdue += amount
                            no_days = (today - aml['date_maturity']).days
                            sheet.write(row_num, col_num + 3, aml['invoice'] if aml['invoice'] else aml['entry'], format6)
                            sheet.write(row_num, col_num + 4, aml['date_maturity'], date_time_default_col1_style_2)
                            sheet.write(row_num, col_num + 5, no_days, format7)
                            sheet.write(row_num, col_num + 6, aml['amount_residual'], format8)
                            row_num += 1
                    sheet.write(row_old, col_num + 7, total_overdue, format5)
                else:
                    for aml in unreconciled_aml_ids:
                        if aml['company_id'] == self.env.user.company_id.id:
                            amount = aml['amount_residual']
                            total_overdue += amount
                            no_days = (today - aml['date_maturity']).days
                            sheet.write(row_num, col_num, record.name, format3)
                            sheet.write(row_num, col_num + 1, record.email if record.email else '', format3)
                            sheet.write(row_num, col_num + 2, record.phone if record.phone else '', format3)
                            sheet.write(row_num, col_num + 3, aml['invoice'] if aml['invoice'] else aml['entry'], format3)
                            sheet.write(row_num, col_num + 4, aml['date_maturity'], date_time_default_col1_style)
                            sheet.write(row_num, col_num + 5, no_days, format4)
                            sheet.write(row_num, col_num + 6, aml['amount_residual'], format4)
                            sheet.write(row_num, col_num + 7, total_overdue, format5)
                            row_num += 1

