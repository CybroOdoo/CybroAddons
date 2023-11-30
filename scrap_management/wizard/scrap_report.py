# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import io
import json
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ScrapReport(models.TransientModel):
    """Transient model to give the input values for the
    generation of report values"""
    _name = "scrap.report"
    _description = "Scrap Report Wizard"

    from_date = fields.Date(string="From Date", help="From this date report"
                                                     "values are taken")
    to_date = fields.Date(string="To Date", help="To this date the report "
                                                 "values are taken")
    product_id = fields.Many2one('product.product', string="Product",
                                 help="choose the product of which the detail "
                                      "should be known")

    def action_pdf_report(self):
        """ To pass values in wizard"""
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise ValidationError(_("From Date can't be greater than"
                                      " to date"))
        if self.from_date:
            if self.from_date > fields.Date.today():
                raise ValidationError(_("From date cannot be future date"))
        data = {
            'model_id': self.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'product_id': self.product_id.product_tmpl_id.id,
        }
        return self.env.ref(
            'scrap_management.scrap_order_report').report_action(
            None, data=data)

    def action_xlsx_report(self):
        """ To print the XLSX report type"""
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise ValidationError(_("From date can't be greater than "
                                      "To date"))
        if self.from_date:
            if self.from_date > fields.Date.today():
                raise ValidationError(_("From date cannot be future date"))
        query = self.env[
            'report.scrap_management.report_scrap_order'].query_data(
            self.from_date, self.to_date, self.product_id.product_tmpl_id.id)
        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'product_id': self.product_id.product_tmpl_id.id,
            'var': query
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'scrap.report',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Scrap Order Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """To get the report values for xlsx report"""
        from_date = data['from_date']
        to_date = data['to_date']
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {'font_size': '12px', 'bold': True, 'align': 'center'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})
        txt_head = workbook.add_format({'font_size': '10px', 'align': 'left',
                                        'bold': True})
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 10)
        sheet.set_column(2, 2, 10)
        sheet.merge_range('A1:B1', 'Report Date:'+str(fields.Date.today()),
                          txt_head)
        sheet.merge_range('A2:D3', 'SCRAP ORDER REPORT', head)
        if from_date:
            sheet.write('A4', 'From Date:', txt_head)
            sheet.write('A5', from_date, txt)
        if to_date:
            sheet.write('B4', 'To Date:', txt_head)
            sheet.write('B5', to_date, txt)
        sheet.write('A6', 'Product', cell_format)
        sheet.write('B6', 'Quantity', cell_format)
        sheet.write('C6', 'Date', cell_format)
        row = 6
        for records in data['var']:
            sheet.write(row, 0, records['product']['en_US'], txt)
            sheet.write(row, 1, records['quantity'], txt)
            sheet.write(row, 2, records['date'], txt)
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
