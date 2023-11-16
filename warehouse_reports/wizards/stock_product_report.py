# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import io
import json
import xlsxwriter
from odoo import fields, models
from odoo.tools import date_utils


class StockProductReport(models.TransientModel):
    """ Wizard for printing product report.Both excel and pdf can be print
        by filtering the data"""
    _name = "stock.product.report"
    _description = "Stock Product Report"

    product_id = fields.Many2one('product.product', string="Product",
                                 help='Used to select product')
    product_category_id = fields.Many2one('product.category', required=True,
                                          string="Product Category",
                                          help="To pick the product category")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='To pick the company')
    from_date = fields.Datetime(string="Date from",
                                help='Stock move start from')
    to_date = fields.Datetime(string='To date', help='Stock move end')

    def action_print_pdf_report(self):
        """ Function to print pdf report passing value to the pdf report"""
        lang = f"'{self.env.context['lang']}'"
        query = """WITH RECURSIVE CategoryHierarchy AS (SELECT id,name,parent_id
        FROM product_category WHERE id = {} UNION ALL SELECT c.id, c.name, 
        c.parent_id FROM product_category c JOIN CategoryHierarchy ch ON 
        c.parent_id = ch.id) SELECT CategoryHierarchy.id as category_id,
        CategoryHierarchy.name as category_name,
        product_template.name->>{} as product_name,
        product_product.outgoing_qty,
        product_product.incoming_qty,
        product_product.free_qty,
        product_product.qty_available 
        FROM CategoryHierarchy
        JOIN product_category on CategoryHierarchy.id = product_category.id
        JOIN product_template on product_category.id = product_template.categ_id
        JOIN product_product on product_template.id = product_product.product_tmpl_id""".format(
            self.product_category_id.id, lang)
        product_id = self.product_id.id
        if self.product_id:
            self.env.cr.execute(
                """{} and product_product.id = '{}' """.format(
                    query, product_id))
        else:
            self.env.cr.execute("""{}""".format(query))
        stock_product = self.env.cr.dictfetchall()
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_product': stock_product
        }
        return self.env.ref(
            'warehouse_reports.stock_product_report').report_action(
            None, data=data)

    def action_print_xls_report(self):
        """ function to pass data to Excel report"""
        lang = f"'{self.env.context['lang']}'"
        query = """WITH RECURSIVE CategoryHierarchy AS (SELECT id,name,parent_id
                FROM product_category WHERE id = {} UNION ALL SELECT c.id, 
                c.name, c.parent_id FROM product_category c 
                JOIN CategoryHierarchy ch ON c.parent_id = ch.id) SELECT 
                CategoryHierarchy.id as category_id,
                CategoryHierarchy.name as category_name,
                product_template.name->>{} as product_name,
                product_product.outgoing_qty,
                product_product.incoming_qty,
                product_product.free_qty,
                product_product.qty_available 
                FROM CategoryHierarchy
                JOIN product_category on CategoryHierarchy.id = product_category.id
                JOIN product_template on product_category.id = product_template.categ_id
                JOIN product_product on product_template.id = product_product.product_tmpl_id""".format(
            self.product_category_id.id, lang)
        product_id = self.product_id.id
        if self.product_id:
            self.env.cr.execute(
                """{} and product_product.id = '{}' """.format(
                    query, product_id))
        else:
            self.env.cr.execute("""{}""".format(query))
        stock_product = self.env.cr.dictfetchall()
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_product': stock_product,
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.product.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Stock Product Report'}}

    def get_xlsx_report(self, data, response):
        """ function to print Excel report and customising the Excel file
            :param data :Dictionary contains results
            :param response : Response from the controller"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 8, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('B2:D3', 'STOCK REPORT', head)
        sheet.merge_range('B4:D4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Product Name', txt)
        sheet.write('C8', 'Product Category', txt)
        sheet.write('D8', 'On Hand Quantity', txt)
        sheet.write('E8', 'Quantity Unreserved', txt)
        sheet.write('F8', 'Incoming Quantity', txt)
        sheet.write('G8', 'Outgoing Quantity', txt)
        records = data['stock_product']
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['product_name'], txt)
            sheet.write(row, 2, record['category_name'], txt)
            sheet.write(row, 3, record['outgoing_qty'], txt)
            sheet.write(row, 4, record['incoming_qty'], txt)
            sheet.write(row, 5, record['free_qty'], txt)
            sheet.write(row, 6, record['qty_available'], txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
