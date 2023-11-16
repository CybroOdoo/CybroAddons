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


class StockValuationReport(models.TransientModel):
    """ Wizard for printing stock valuation report.We will get both excl
        and pdf reports"""
    _name = "stock.valuation.report"
    _description = "Stock Valuation Report"

    product_id = fields.Many2one('product.product', string='Product',
                                 help='To pick the product')
    product_category_id = fields.Many2one('product.category',
                                          string='Product Category', required=True,
                                          help='To pick product_category')
    from_Date = fields.Datetime(string='From Date', required=True,
                                default=fields.Datetime.now(),
                                help='For filtering data using from date')
    to_date = fields.Datetime(string='To Date', required=True,
                              default=fields.Datetime.now(),
                              help='For filtering data using to date')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)

    def action_print_pdf_report(self):
        """ Function to print pdf report.Passing data to pdf template"""
        lang = f"'{self.env.context['lang']}'"
        query = """ WITH RECURSIVE CategoryHierarchy AS ( SELECT id,name, 
                    parent_id FROM product_category WHERE id = {} UNION ALL 
                    SELECT c.id, c.name, c.parent_id FROM product_category c
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id)
                    SELECT CategoryHierarchy.id as category_id, 
                    CategoryHierarchy.name as category_name,
                    stock_valuation_layer.create_date, product_template.name->>{}
                     as name, stock_valuation_layer.description, 
                     product_category.complete_name,res_company.name as 
                     company_name, quantity, stock_valuation_layer.unit_cost, 
                     value FROM CategoryHierarchy JOIN product_category on 
                     CategoryHierarchy.id = product_category.id JOIN 
                     product_template on product_category.id = 
                     product_template.categ_id JOIN product_product on 
                     product_template.id = product_product.product_tmpl_id JOIN
                      stock_valuation_layer on product_product.id = 
                      stock_valuation_layer.product_id JOIN res_company on 
                      stock_valuation_layer.company_id = res_company.id
                 """.format(self.product_category_id.id, lang)
        product_id = self.product_id.id
        company_id = self.company_id.id
        from_date = self.from_Date
        to_date = self.to_date
        if self.product_id and self.company_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and stock_valuation_layer.company_id
                 ='{}' and stock_valuation_layer.create_date >='{}' 
                 and stock_valuation_layer.create_date<'{}'""".format(
                    query, product_id, company_id,
                    from_date,
                    to_date))
        elif self.product_id and self.company_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and 
                stock_valuation_layer.company_id ='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, product_id, company_id, from_date,
                    to_date))
        elif self.product_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, product_id, from_date, to_date))
        elif self.company_id:
            self.env.cr.execute(
                """{} where stock_valuation_layer.company_id='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, company_id, from_date, to_date))
        else:
            self.env.cr.execute("""{}""".format(query))
        stock_valuation = self.env.cr.dictfetchall()
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_valuation': stock_valuation
        }
        return self.env.ref(
            'warehouse_reports.stock_valuation_report').report_action(
            None, data=data)

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file"""
        lang = f"'{self.env.context['lang']}'"
        query = """ WITH RECURSIVE CategoryHierarchy AS ( SELECT id,name, 
                    parent_id FROM product_category WHERE id = {} UNION ALL 
                    SELECT c.id, c.name, c.parent_id FROM product_category c
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id)
                    SELECT CategoryHierarchy.id as category_id, 
                    CategoryHierarchy.name as category_name,
                    stock_valuation_layer.create_date, product_template.name->>{}
                     as name, stock_valuation_layer.description, 
                     product_category.complete_name,res_company.name as 
                     company_name, quantity, stock_valuation_layer.unit_cost, 
                     value FROM CategoryHierarchy JOIN product_category on 
                     CategoryHierarchy.id = product_category.id JOIN 
                     product_template on product_category.id = 
                     product_template.categ_id JOIN product_product on 
                     product_template.id = product_product.product_tmpl_id JOIN
                      stock_valuation_layer on product_product.id = 
                      stock_valuation_layer.product_id JOIN res_company on 
                      stock_valuation_layer.company_id = res_company.id
                 """.format(self.product_category_id.id, lang)
        product_id = self.product_id.id
        company_id = self.company_id.id
        from_date = self.from_Date
        to_date = self.to_date
        if self.product_id and self.company_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and stock_valuation_layer.company_id
                 ='{}' and stock_valuation_layer.create_date >='{}' 
                 and stock_valuation_layer.create_date<'{}'""".format(
                    query, product_id, company_id,
                    from_date,
                    to_date))
        elif self.product_id and self.company_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and 
                stock_valuation_layer.company_id ='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, product_id, company_id, from_date,
                    to_date))
        elif self.product_id:
            self.env.cr.execute(
                """{}where product_product.id='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, product_id, from_date, to_date))
        elif self.company_id:
            self.env.cr.execute(
                """{} where stock_valuation_layer.company_id='{}' and 
                stock_valuation_layer.create_date >='{}' and 
                stock_valuation_layer.create_date<'{}'""".format(
                    query, company_id, from_date, to_date))
        else:
            self.env.cr.execute("""{}""".format(query))
        stock_valuation = self.env.cr.dictfetchall()
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'vehicle_id': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_valuation': stock_valuation
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.valuation.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Stock valuation report'}}

    def get_xlsx_report(self, data, response):
        """ Function to print excel report.Customizing excel file and added data
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
        sheet.merge_range('C4:E4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Date', txt)
        sheet.write('C8', 'Product Name', txt)
        sheet.write('D8', 'Description', txt)
        sheet.write('E8', 'Product Category', txt)
        sheet.write('F8', 'Company Name', txt)
        sheet.write('G8', 'Quantity', txt)
        sheet.write('H8', 'Unit Cost', txt)
        sheet.write('I8', 'Value', txt)
        records = data['stock_valuation']
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['create_date'], txt)
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
