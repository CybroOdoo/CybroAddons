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


class StockMoveReport(models.TransientModel):
    """ Wizard for printing stock move report.We can filter data by
        product,location,product category etc."""
    _name = "stock.move.report"
    _description = "Stock Move Report"

    product_id = fields.Many2one('product.product', string='Product',
                                 help='To pick the product')
    location_id = fields.Many2one('stock.location', string='Location',
                                  help='Pick stock location')
    product_category_id = fields.Many2one('product.category',
                                          string='Product Category', required=True,
                                          help='To pick product_category')
    from_date = fields.Datetime(string="Date from",
                                help='Stock move start from date',
                                required=True, default=fields.Datetime.now())
    to_date = fields.Datetime(string='To date', help='Stock move end date',
                              required=True, default=fields.Datetime.now())
    company_id = fields.Many2one('res.company', string="Company",
                                 help="For adding company details",
                                 default=lambda self: self.env.company)

    def action_print_pdf_report(self):
        """ Function to print pdf report data filtered and passed to
            the template"""
        state = {'draft': 'New', 'cancel': 'cancelled',
                 'waiting': 'Waiting Another Move',
                 'confirmed': 'Waiting Availability',
                 'partially_available': 'Partially Available',
                 'assigned': 'Available', 'done': 'Done'}
        lang = f"'{self.env.context['lang']}'"
        query = """ WITH RECURSIVE CategoryHierarchy AS (SELECT id,name,
                    parent_id,complete_name FROM product_category WHERE
                    id = '{}' UNION ALL SELECT c.id, c.name, c.parent_id,
                    c.complete_name FROM product_category c JOIN 
                    CategoryHierarchy ch ON c.parent_id = ch.id)
                    SELECT stock_move.date, stock_move.reference, 
                    product_template.name, stock_location.complete_name,
                    product_category.complete_name as category_name,
                    stock_move.product_uom_qty,res_company.name, 
                    stock_move.state,product_template.name->>{} as product_name
                    FROM stock_move JOIN product_product ON 
                    stock_move.product_id = product_product.id
                    JOIN stock_location ON 
                    stock_move.location_id = stock_location.id
                    JOIN product_template ON 
                    product_product.product_tmpl_id = product_template.id
                    JOIN product_category ON 
                    product_template.categ_id = product_category.id
                    JOIN res_company ON 
                    stock_move.company_id = res_company.id WHERE
                    product_category.id IN (SELECT id FROM CategoryHierarchy)""".format(
            self.product_category_id.id, lang)
        product_id = self.product_id.id
        location_id = self.location_id.id
        company_id = self.company_id.id
        from_date = self.from_date
        to_date = self.to_date
        if self.product_id and self.location_id and self.company_id and \
                self.from_date and self.to_date:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}' and stock_move.company_id = '{}'
                 and stock_move.date >='{}' and 
                 stock_move.date<'{}'""".format(
                    query, product_id, location_id, company_id, from_date,
                    to_date))
        elif self.product_id and self.location_id and self.company_id and self.from_date:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}' and stock_move.company_id = '{}' 
                 and stock_move.date >='{}' and 
                stock_move.date<'{}'""".format(
                    query, product_id, location_id, company_id,
                    from_date, to_date))
        elif self.product_id and self.location_id and self.company_id:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}' and stock_move.company_id = '{}' and stock_move.date >='{}' and
                  stock_move.date<'{}'""".format(
                    query, product_id, location_id, company_id,
                    from_date, to_date))
        elif self.product_id and self.location_id and self.company_id:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}' and stock_move.company_id = '{}'
                 and stock_move.date >='{}' and stock_move.date<'{}'""".format(
                    query, product_id, location_id, company_id, from_date,
                    to_date))
        elif self.company_id and self.location_id:
            self.env.cr.execute(
                """{}and stock_move.company_id = '{}' and stock_move.location_id = '{}' 
                and stock_move.date <='{}' and stock_move.date<'{}'""".format(
                    query, company_id, location_id, from_date,
                    to_date))
        elif self.product_id and self.location_id:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}'""".format(
                    query, product_id, location_id, from_date, to_date))
        elif self.product_id and self.company_id.id:
            self.env.cr.execute(
                """{} and stock_move.company_id={} and product_template.id={} and 
                stock_move.date >='{}' and stock_move.date<'{}'""".format(
                    query,
                    company_id, product_id, from_date, to_date))
        elif self.product_id:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.date >='{}' and stock_move.date<'{}'""".format(
                    query, product_id, from_date, to_date))
        elif self.company_id:
            self.env.cr.execute(
                """{}and stock_move.company_id='{}' and 
                stock_move.date >='{}' and stock_move.date<'{}'""".format(
                    query, company_id, from_date, to_date))
        else:
            self.env.cr.execute("""{}""".format(query))
        stock_move = self.env.cr.dictfetchall()
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'location': self.location_id.complete_name,
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_move': stock_move,
            'status': state
        }
        return self.env.ref(
            'warehouse_reports.stock_move_report').report_action(
            None, data=data)

    def action_print_xls_report(self):
        """ Function to filter and pass values to the Excel report template"""
        lang = f"'{self.env.context['lang']}'"
        query = """ WITH RECURSIVE CategoryHierarchy AS (SELECT id,name,
                    parent_id,complete_name FROM product_category WHERE
                    id = '{}' UNION ALL SELECT c.id, c.name, c.parent_id,
                    c.complete_name FROM product_category c JOIN 
                    CategoryHierarchy ch ON c.parent_id = ch.id)
                    SELECT stock_move.date, stock_move.reference, 
                    product_template.name, stock_location.complete_name,
                    product_category.complete_name as category_name,
                    stock_move.product_uom_qty,res_company.name, 
                    stock_move.state,product_template.name->>{} as product_name
                    FROM stock_move JOIN product_product ON 
                    stock_move.product_id = product_product.id
                    JOIN stock_location ON 
                    stock_move.location_id = stock_location.id
                    JOIN product_template ON 
                    product_product.product_tmpl_id = product_template.id
                    JOIN product_category ON 
                    product_template.categ_id = product_category.id
                    JOIN res_company ON 
                    stock_move.company_id = res_company.id WHERE
                    product_category.id IN (SELECT id FROM CategoryHierarchy)""".format(
            self.product_category_id.id, lang)
        product_id = self.product_id.id
        location_id = self.location_id.id
        company_id = self.company_id.id
        from_date = self.from_date
        to_date = self.to_date
        if self.product_id and self.location_id and self.company_id and \
                self.from_date and self.to_date:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}' and stock_move.company_id = '{}'
                 and stock_move.date >='{}' and 
                 stock_move.date<'{}'""".format(
                    query, product_id, location_id, company_id, from_date,
                    to_date))
        elif self.product_id and self.location_id and self.company_id and self.from_date:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}' and stock_move.company_id = '{}' 
                 and stock_move.date >='{}' and 
                stock_move.date<'{}'""".format(
                    query, product_id, location_id, company_id,
                    from_date, to_date))
        elif self.product_id and self.location_id and self.company_id:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}' and stock_move.company_id = '{}' and stock_move.date >='{}' and
                  stock_move.date<'{}'""".format(
                    query, product_id, location_id, company_id,
                    from_date, to_date))
        elif self.product_id and self.location_id and self.company_id:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}' and stock_move.company_id = '{}'
                 and stock_move.date >='{}' and stock_move.date<'{}'""".format(
                    query, product_id, location_id, company_id, from_date,
                    to_date))
        elif self.company_id and self.location_id:
            self.env.cr.execute(
                """{}and stock_move.company_id = '{}' and stock_move.location_id = '{}' 
                and stock_move.date <='{}' and stock_move.date<'{}'""".format(
                    query, company_id, location_id, from_date,
                    to_date))
        elif self.product_id and self.location_id:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.location_id ='{}'""".format(
                    query, product_id, location_id, from_date, to_date))
        elif self.product_id and self.company_id.id:
            self.env.cr.execute(
                """{} and stock_move.company_id={} and product_template.id={} and 
                stock_move.date >='{}' and stock_move.date<'{}'""".format(
                    query,
                    company_id, product_id, from_date, to_date))
        elif self.product_id:
            self.env.cr.execute(
                """{}and stock_move.product_id='{}' and 
                stock_move.date >='{}' and stock_move.date<'{}'""".format(
                    query, product_id, from_date, to_date))
        elif self.company_id:
            self.env.cr.execute(
                """{}and stock_move.company_id='{}' and 
                stock_move.date >='{}' and stock_move.date<'{}'""".format(
                    query, company_id, from_date, to_date))
        else:
            self.env.cr.execute("""{}""".format(query))
        stock_move = self.env.cr.dictfetchall()
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'location': self.location_id.complete_name,
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_move': stock_move
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.move.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Stock Move report'}
        }

    def get_xlsx_report(self, data, response):
        """ Function to print excel report customize the Excel file for
            print data
             :param data :Dictionary contains results
            :param response : Response from the controller"""
        state = {'draft': 'New', 'cancel': 'cancelled',
                 'waiting': 'Waiting Another Move',
                 'confirmed': 'Waiting Availability',
                 'partially_available': 'Partially Available',
                 'assigned': 'Available', 'done': 'Done'}
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'align': 'center'})
        sheet.set_column(0, 8, 24)
        sheet.merge_range('B2:D3', 'STOCK MOVE REPORT', head)
        sheet.merge_range('B4:D4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Date', txt)
        sheet.write('C8', 'Reference', txt)
        sheet.write('D8', 'Product', txt)
        sheet.write('E8', 'Location', txt)
        sheet.write('F8', 'Quantity', txt)
        sheet.write('G8', 'Company', txt)
        sheet.write('H8', 'Product Category', txt)
        sheet.write('I8', 'Status', txt)
        records = data['stock_move']
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['date'])
            sheet.write(row, 2, record['reference'])
            sheet.write(row, 3, record['product_name'])
            sheet.write(row, 4, record['complete_name'])
            sheet.write(row, 5, record['product_uom_qty'], txt)
            sheet.write(row, 6, record['name'])
            sheet.write(row, 7, record['category_name'])
            sheet.write(row, 8, state[record['state']], txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
