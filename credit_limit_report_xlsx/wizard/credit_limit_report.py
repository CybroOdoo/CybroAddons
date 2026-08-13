# -*- coding: utf-8 -*-
###############################################################################

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ATHUL RAJ B S(Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
import io
from odoo import fields, models

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class CreditLimitReport(models.TransientModel):
    """This is an abstract wizard class
        xlsx_credit_limit_report(self, data):
            button function for xlsx creation"""
    _name = 'credit.limit.report'
    _description = "Credit Limit Report Wizard"

    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Select Customer from here")

    def action_print_report(self):
        """This is a function that returns a dictionary with the
            data needed to generate an Excel report for credit limit """
        return {
            'type': 'ir.actions.report',
            'report_type': 'credit_limit_xlsx',
            'data': {
                'output_format': 'xlsx',
                'wizard_id': self.id,
            },
        }

    def get_xlsx_report(self, response, wizard_id=None):
        """Generate and write data to a xlsx report."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Credit Limit Report')
        format1 = workbook.add_format(
            {'font_size': 20, 'align': 'center', 'bg_color': '#cecece',
             'bold': True})
        format2 = workbook.add_format(
            {'align': 'center', 'font_size': 11, 'bg_color': '#cecece',
             'bold': True, 'border': 1})
        format3 = workbook.add_format(
            {'align': 'left', 'font_size': 10, 'border': 1})
        format4 = workbook.add_format({'font_size': 12, 'align': 'left'})
        format5 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'border': 1})
        sheet.set_row(0, 30)
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        partner_ids = []
        
        # Prefer the passed wizard ID, fallback to the last created one
        if wizard_id:
            credit_limit_report = self.browse(int(wizard_id))
        else:
            credit_limit_report = self.search([], limit=1, order='id desc')
            
        if credit_limit_report:
            sheet.merge_range('A3:C3',
                              'Report Date: ' + fields.Datetime.now().strftime(
                                  "%Y-%m-%d"), format4)

            if credit_limit_report.customer_id:
                partner = credit_limit_report.customer_id
                sheet.merge_range('A4:C4',
                                  'Customer Name: ' + partner.name,
                                  format4)
                if partner.use_partner_credit_limit:
                    partner_ids = [partner.id]
                else:
                    sheet.merge_range('A7:C7',
                                      'There is no credit limit activated for this customer',
                                      format5)
            else:
                # Use ORM search for computed 'credit' field
                partners = self.env['res.partner'].search([('credit', '>', 0)])
                partner_ids = partners.ids
        else:
            sheet.merge_range('A1:D1', 'No credit limit report found', format1)
            workbook.close()
            output.seek(0)
            response.stream.write(output.read())
            output.close()
            return

        header_row = ['EMAIL', 'PHONE', 'DUE AMOUNT']
        col_formats = [format2, format2, format2]
        sheet.merge_range('A1:C1', 'CREDIT LIMIT EXCEED REPORT', format1)
        if not credit_limit_report or not credit_limit_report.customer_id:
            sheet.merge_range('A1:D1', 'CREDIT LIMIT EXCEED REPORT', format1)
            header_row = ['PARTNER'] + header_row
            col_formats = [format2] + col_formats
        for col, (header, col_format) in enumerate(
                zip(header_row, col_formats)):
            sheet.write(5, col, header, col_format)
        row_num = 6
        col_num = 0
        for pid in partner_ids:
            partner = self.env['res.partner'].browse(pid)
            # Display only partners who exceed their limit
            if partner and (partner.credit > partner.credit_limit):
                if credit_limit_report and credit_limit_report.customer_id:
                    sheet.write(row_num, col_num, partner.email or '', format3)
                    sheet.write(row_num, col_num + 1, partner.phone or '',
                                format3)
                    sheet.write(row_num, col_num + 2, partner.credit, format3)
                else:
                    sheet.write(row_num, col_num, partner.name, format3)
                    sheet.write(row_num, col_num + 1, partner.email or '',
                                format3)
                    sheet.write(row_num, col_num + 2, partner.phone or '',
                                format3)
                    sheet.write(row_num, col_num + 3, partner.credit, format3)
                row_num += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
