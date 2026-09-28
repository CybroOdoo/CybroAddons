# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import io
import json
import xlsxwriter
from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import json_default


class StockValuationReport(models.TransientModel):
    """ Wizard for printing stock valuation report in PDF and Excel formats."""
    _name = "stock.valuation.report"
    _description = "Stock Valuation Report"

    product_id = fields.Many2one('product.product', string='Product',
                                 help='To pick the product')
    product_category_id = fields.Many2one('product.category',
                                          string='Product Category', required=True,
                                          help='To pick product_category')
    from_Date = fields.Datetime(string='From Date', required=True,
                                default=fields.Datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0),
                                help='For filtering data using from date')
    to_date = fields.Datetime(string='To Date', required=True,
                              default=fields.Datetime.now(),
                              help='For filtering data using to date')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    def _get_stock_valuation_data(self):
        """ Internal method to validate filters and fetch stock valuation records."""
        if self.from_Date and self.to_date and self.to_date < self.from_Date:
            raise ValidationError(_('Sorry, To Date Must be greater Than or equal to From Date...'))

        lang = self.env.context.get('lang', 'en_US')
        query = """ WITH RECURSIVE CategoryHierarchy AS (
                        SELECT id, name, parent_id FROM product_category WHERE id = %s
                        UNION ALL 
                        SELECT c.id, c.name, c.parent_id FROM product_category c
                        JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                    )
                    SELECT 
                        CategoryHierarchy.id as category_id, 
                        CategoryHierarchy.name as category_name,
                        stock_valuation_layer.create_date, 
                        COALESCE(product_template.name->>%s, product_template.name->>'en_US', product_template.name::text) as name, 
                        stock_valuation_layer.description, 
                        product_category.complete_name,
                        res_company.name as company_name, 
                        stock_valuation_layer.quantity, 
                        stock_valuation_layer.unit_cost, 
                        stock_valuation_layer.value 
                    FROM CategoryHierarchy 
                    JOIN product_category on CategoryHierarchy.id = product_category.id 
                    JOIN product_template on product_category.id = product_template.categ_id 
                    JOIN product_product on product_template.id = product_product.product_tmpl_id 
                    JOIN stock_valuation_layer on product_product.id = stock_valuation_layer.product_id 
                    JOIN res_company on stock_valuation_layer.company_id = res_company.id
                    WHERE 1=1
                 """
        params = [self.product_category_id.id, lang]

        if self.product_id:
            query += " AND product_product.id = %s"
            params.append(self.product_id.id)
        if self.company_id:
            query += " AND stock_valuation_layer.company_id = %s"
            params.append(self.company_id.id)
        if self.from_Date:
            query += " AND stock_valuation_layer.create_date >= %s"
            params.append(self.from_Date)
        if self.to_date:
            query += " AND stock_valuation_layer.create_date <= %s"
            params.append(self.to_date)

        query += " ORDER BY stock_valuation_layer.create_date DESC"

        self.env.cr.execute(query, params)
        stock_valuation = self.env.cr.dictfetchall()

        if not stock_valuation:
            raise UserError(_("No data found for the selected criteria."))

        return stock_valuation

    def action_print_pdf_report(self):
        """ Function to print pdf report. Passing data to pdf template."""
        stock_valuation = self._get_stock_valuation_data()
        data = {
            'product_name': self.product_id.product_tmpl_id.name if self.product_id else '',
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name if self.company_id else '',
            'company_street': self.company_id.street if self.company_id else '',
            'state': self.company_id.state_id.name if self.company_id and self.company_id.state_id else '',
            'country': self.company_id.country_id.name if self.company_id and self.company_id.country_id else '',
            'company_email': self.company_id.email if self.company_id else '',
            'stock_valuation': stock_valuation
        }
        return self.env.ref(
            'report_stock_inventory.stock_valuation_report').report_action(
            self.ids, data=data)

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file."""
        stock_valuation = self._get_stock_valuation_data()
        data = {
            'product_name': self.product_id.product_tmpl_id.name if self.product_id else '',
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name if self.company_id else '',
            'company_street': self.company_id.street if self.company_id else '',
            'state': self.company_id.state_id.name if self.company_id and self.company_id.state_id else '',
            'country': self.company_id.country_id.name if self.company_id and self.company_id.country_id else '',
            'company_email': self.company_id.email if self.company_id else '',
            'stock_valuation': stock_valuation
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.valuation.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=json_default),
                     'report_name': 'Stock valuation report'}}

    def get_xlsx_report(self, data, response):
        """ Function to print excel report. Customizing excel file and added data
            :param data :Dictionary contains results
            :param response : Response from the controller"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 10, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('C2:E3', 'STOCK VALUATION REPORT', head)
        sheet.merge_range('C4:E4', data.get('company_name', ''), txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Date', txt)
        sheet.write('C8', 'Product Name', txt)
        sheet.write('D8', 'Description', txt)
        sheet.write('E8', 'Product Category', txt)
        sheet.write('F8', 'Company Name', txt)
        sheet.write('G8', 'Quantity', txt)
        sheet.write('H8', 'Unit Cost', txt)
        sheet.write('I8', 'Value', txt)
        records = data.get('stock_valuation', [])
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, str(record['create_date']), txt)
            sheet.write(row, 2, record['name'], txt)
            sheet.write(row, 3, record['description'], txt)
            sheet.write(row, 4, record['complete_name'], txt)
            sheet.write(row, 5, record['company_name'], txt)
            sheet.write(row, 6, record['quantity'], txt)
            sheet.write(row, 7, record['unit_cost'], txt)
            sheet.write(row, 8, record['value'], txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
