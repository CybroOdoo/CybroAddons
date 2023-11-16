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


class StockTransferReport(models.TransientModel):
    """ Wizard to getting the stock transfer reports.We can get both Pdf and
        Excel report """
    _name = "stock.transfer.report"
    _description = "Stock Transfer Report"

    product_id = fields.Many2one('product.product', string='Product',
                                 help='To pick the product')
    location_id = fields.Many2one('stock.location', string='Location',
                                  help='Pick stock location')
    product_category_id = fields.Many2one('product.category', required=True,
                                          string='Product Category',
                                          help='To pick product_category')
    picking_type_id = fields.Many2one('stock.picking.type',
                                      string="Operation Type",
                                      help='To select the operation type')
    partner_id = fields.Many2one('res.partner', string='Customer/Vendor',
                                 help='To pick the vendor/customer')
    from_date = fields.Datetime(string="Date from",
                                help='Stock move start from',
                                required=True, default=fields.Datetime.now())
    to_date = fields.Datetime(string='To date', help='Stock move end',
                              required=True, default=fields.Datetime.now())
    company_id = fields.Many2one('res.company', string='Company Name',
                                 default=lambda self: self.env.company,
                                 help='To pick company')

    def action_print_pdf_report(self):
        """ function to print pdf report .Value passed to the pdf template"""
        state = {'draft': 'Draft', 'waiting': 'Waiting Another Operation',
                 'confirmed': 'Waiting', 'assigned': 'Ready', 'done': 'Done',
                 'cancel': 'Cancelled'}
        lang = f"'{self.env.context['lang']}'"
        query = """WITH RECURSIVE CategoryHierarchy AS (SELECT id,name,parent_id
                    FROM product_category WHERE id = {} UNION ALL 
                    SELECT c.id,c.name, c.parent_id FROM 
                    product_category c JOIN CategoryHierarchy ch ON
                    c.parent_id = ch.id) SELECT CategoryHierarchy.id 
                    as category_id, CategoryHierarchy.name as 
                    category_name, stock_picking.name as picking_name,
                    product_template.name->>{} as product_name,
                    stock_picking.scheduled_date, stock_picking.date_deadline,
                    stock_picking.date_done, stock_picking.origin,
                    stock_location.complete_name,stock_picking_type.display_name,
                    res_company.name as company_name,stock_picking.state 
                    FROM CategoryHierarchy
                    JOIN product_category on CategoryHierarchy.id =
                    product_category.id JOIN product_template on 
                    product_category.id = product_template.categ_id
                    JOIN product_product on product_template.id = 
                    product_product.product_tmpl_id JOIN stock_move on
                    product_product.id = stock_move.product_id
                    JOIN stock_picking on stock_move.picking_id = 
                    stock_picking.id JOIN stock_picking_type on 
                    stock_picking.picking_type_id = stock_picking_type.id
                    JOIN res_company on stock_picking.company_id = 
                    res_company.id JOIN stock_location on 
                    stock_move.location_id = stock_location.id""".format(
            self.product_category_id.id, lang)
        product_id = self.product_id.id
        location_id = self.location_id.id
        from_date = self.from_date
        to_date = self.to_date
        company_id = self.company_id.id
        partner_id = self.partner_id.id
        picking_type_id = self.picking_type_id.id
        if self.product_id and self.location_id and self.partner_id and picking_type_id:
            self.env.cr.execute(
                """{} and product_product.id = '{}' and 
                stock_picking.company_id ='{}' and 
                stock_move.location_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' and 
                stock_picking.partner_id = '{}' and 
                stock_picking.picking_type_id = '{}' """.format(
                    query, product_id, company_id, location_id,
                    from_date, to_date, partner_id, picking_type_id))
        elif self.product_id and self.location_id and self.partner_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.company_id ='{}' 
                and stock_move.location_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' and 
                stock_picking.partner_id = '{}' """.format(
                    query, product_id, company_id, location_id,
                    from_date, to_date, partner_id))
        elif self.product_id and self.location_id and self.picking_type_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.picking_type_id 
                ='{}' and stock_move.location_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, picking_type_id, location_id,
                    from_date, to_date
                ))
        elif self.product_id and self.company_id and self.picking_type_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.company_id ='{}' 
                and stock_picking.picking_type_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, company_id, picking_type_id,
                    from_date, to_date
                ))
        elif self.product_id and self.location_id and self.company_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.company_id ='{}' 
                and stock_move.location_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, company_id, location_id,
                    from_date, to_date
                ))
        elif self.product_id and self.location_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_location.id ='{}' 
                and stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, location_id, from_date,
                    to_date))
        elif self.product_id and self.picking_type_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and 
                stock_picking.picking_type_id='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, picking_type_id, from_date,
                    to_date))
        elif self.product_id and self.company_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.company_id 
                ='{}' and stock_picking.scheduled_date>='{}' 
                and stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, company_id, from_date,
                    to_date))
        elif self.product_id and self.company_id and self.location_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and 
                stock_picking.company_id ='{}' and stock_location.id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, company_id, location_id, from_date,
                    to_date))
        elif self.product_id and self.partner_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.partner_id 
                ='{}' and stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, partner_id, from_date,
                    to_date))
        elif self.product_id and self.partner_id and self.location_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and 
                stock_picking.partner_id ='{}' and stock_location.id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, partner_id, location_id, from_date,
                    to_date))
        elif self.company_id and self.location_id:
            self.env.cr.execute(
                """{} where stock_picking.company_id = '{}' and stock_location.id ='{}' 
                and stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, company_id, location_id, from_date,
                    to_date))
        elif self.partner_id and self.location_id:
            self.env.cr.execute(
                """{} where stock_picking.partner_id= '{}' and stock_location.id ='{}' and
                 stock_picking.scheduled_date>='{}' and 
                 stock_picking.scheduled_date >'{}' """.format(
                    query, partner_id, location_id, from_date,
                    to_date))
        elif self.product_id and self.location_id:
            self.env.cr.execute(
                """{} where stock_move.product_id ='{}' and 
                stock_move.location_id = '{}'""".format(query, product_id,
                                                        location_id))
        elif self.product_id and self.partner_id:
            self.env.cr.execute(
                """{} where stock_move.product_id ='{}' and 
                stock_picking.partner_id = '{}'""".format(query, product_id,
                                                          partner_id))
        elif self.product_id and self.company_id:
            self.env.cr.execute(
                """{} where stock_move.product_id ='{}' and 
                stock_picking.company_id = '{}'""".format(query, product_id,
                                                          company_id))
        elif self.company_id and self.partner_id:
            self.env.cr.execute(
                """{} where stock_picking.company_id ='{}' and 
                stock_picking.partner_id = '{}'""".format(query, company_id,
                                                          partner_id))
        elif self.picking_type_id and self.company_id:
            self.env.cr.execute(
                """{} where stock_move.picking_type_id ='{}' and 
                stock_picking.company_id = '{}'""".format(query,
                                                          picking_type_id,
                                                          company_id))
        elif self.product_id:
            self.env.cr.execute(
                """{} where stock_move.product_id ='{}'""".format(query,
                                                                  product_id))
        elif self.location_id:
            self.env.cr.execute(
                """{} where stock_move.location_id ='{}'""".format(query,
                                                                   location_id))
        elif self.partner_id:
            self.env.cr.execute(
                """{} where stock_picking.partner_id ='{}'""".format(query,
                                                                     partner_id))
        elif self.company_id:
            self.env.cr.execute(
                """{} where stock_picking.company_id ='{}'""".format(query,
                                                                     company_id))
        else:
            self.env.cr.execute("""{}""".format(query))
        stock_picking = self.env.cr.dictfetchall()
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'location': self.location_id.complete_name,
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_picking': stock_picking,
            'status': state
        }
        return self.env.ref(
            'warehouse_reports.stock_transfer_report').report_action(
            None, data=data)

    def action_print_xls_report(self):
        """ Function to pass data to the Excel file"""
        lang = f"'{self.env.context['lang']}'"
        query = """WITH RECURSIVE CategoryHierarchy AS (SELECT id,name,parent_id
                    FROM product_category WHERE id = {} UNION ALL 
                    SELECT c.id,c.name, c.parent_id FROM 
                    product_category c JOIN CategoryHierarchy ch ON
                    c.parent_id = ch.id) SELECT CategoryHierarchy.id 
                    as category_id, CategoryHierarchy.name as 
                    category_name, stock_picking.name as picking_name,
                    product_template.name->>{} as product_name,
                    stock_picking.scheduled_date, stock_picking.date_deadline,
                    stock_picking.date_done, stock_picking.origin,
                    stock_location.complete_name,stock_picking_type.display_name,
                    res_company.name as company_name,stock_picking.state 
                    FROM CategoryHierarchy
                    JOIN product_category on CategoryHierarchy.id =
                    product_category.id JOIN product_template on 
                    product_category.id = product_template.categ_id
                    JOIN product_product on product_template.id = 
                    product_product.product_tmpl_id JOIN stock_move on
                    product_product.id = stock_move.product_id
                    JOIN stock_picking on stock_move.picking_id = 
                    stock_picking.id JOIN stock_picking_type on 
                    stock_picking.picking_type_id = stock_picking_type.id
                    JOIN res_company on stock_picking.company_id = 
                    res_company.id JOIN stock_location on 
                    stock_move.location_id = stock_location.id""".format(
            self.product_category_id.id, lang)
        product_id = self.product_id.id
        location_id = self.location_id.id
        from_date = self.from_date
        to_date = self.to_date
        company_id = self.company_id.id
        partner_id = self.partner_id.id
        picking_type_id = self.picking_type_id.id
        if self.product_id and self.location_id and self.partner_id and picking_type_id:
            self.env.cr.execute(
                """{} and product_product.id = '{}' and 
                stock_picking.company_id ='{}' and 
                stock_move.location_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' and 
                stock_picking.partner_id = '{}' and 
                stock_picking.picking_type_id = '{}' """.format(
                    query, product_id, company_id, location_id,
                    from_date, to_date, partner_id, picking_type_id))
        elif self.product_id and self.location_id and self.partner_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.company_id ='{}' 
                and stock_move.location_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' and 
                stock_picking.partner_id = '{}' """.format(
                    query, product_id, company_id, location_id,
                    from_date, to_date, partner_id))
        elif self.product_id and self.location_id and self.picking_type_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.picking_type_id 
                ='{}' and stock_move.location_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, picking_type_id, location_id,
                    from_date, to_date
                ))
        elif self.product_id and self.company_id and self.picking_type_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.company_id ='{}' 
                and stock_picking.picking_type_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, company_id, picking_type_id,
                    from_date, to_date
                ))
        elif self.product_id and self.location_id and self.company_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.company_id ='{}' 
                and stock_move.location_id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, company_id, location_id,
                    from_date, to_date
                ))
        elif self.product_id and self.location_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_location.id ='{}' 
                and stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, location_id, from_date,
                    to_date))
        elif self.product_id and self.picking_type_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and 
                stock_picking.picking_type_id='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, picking_type_id, from_date,
                    to_date))
        elif self.product_id and self.company_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.company_id 
                ='{}' and stock_picking.scheduled_date>='{}' 
                and stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, company_id, from_date,
                    to_date))
        elif self.product_id and self.company_id and self.location_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and 
                stock_picking.company_id ='{}' and stock_location.id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, company_id, location_id, from_date,
                    to_date))
        elif self.product_id and self.partner_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and stock_picking.partner_id 
                ='{}' and stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, partner_id, from_date,
                    to_date))
        elif self.product_id and self.partner_id and self.location_id:
            self.env.cr.execute(
                """{} where product_product.id = '{}' and 
                stock_picking.partner_id ='{}' and stock_location.id ='{}' and 
                stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, product_id, partner_id, location_id, from_date,
                    to_date))
        elif self.company_id and self.location_id:
            self.env.cr.execute(
                """{} where stock_picking.company_id = '{}' and stock_location.id ='{}' 
                and stock_picking.scheduled_date>='{}' and 
                stock_picking.scheduled_date >'{}' """.format(
                    query, company_id, location_id, from_date,
                    to_date))
        elif self.partner_id and self.location_id:
            self.env.cr.execute(
                """{} where stock_picking.partner_id= '{}' and stock_location.id ='{}' and
                 stock_picking.scheduled_date>='{}' and 
                 stock_picking.scheduled_date >'{}' """.format(
                    query, partner_id, location_id, from_date,
                    to_date))
        elif self.product_id and self.location_id:
            self.env.cr.execute(
                """{} where stock_move.product_id ='{}' and 
                stock_move.location_id = '{}'""".format(query, product_id,
                                                        location_id))
        elif self.product_id and self.partner_id:
            self.env.cr.execute(
                """{} where stock_move.product_id ='{}' and 
                stock_picking.partner_id = '{}'""".format(query, product_id,
                                                          partner_id))
        elif self.product_id and self.company_id:
            self.env.cr.execute(
                """{} where stock_move.product_id ='{}' and 
                stock_picking.company_id = '{}'""".format(query, product_id,
                                                          company_id))
        elif self.company_id and self.partner_id:
            self.env.cr.execute(
                """{} where stock_picking.company_id ='{}' and 
                stock_picking.partner_id = '{}'""".format(query, company_id,
                                                          partner_id))
        elif self.picking_type_id and self.company_id:
            self.env.cr.execute(
                """{} where stock_move.picking_type_id ='{}' and 
                stock_picking.company_id = '{}'""".format(query,
                                                          picking_type_id,
                                                          company_id))
        elif self.product_id:
            self.env.cr.execute(
                """{} where stock_move.product_id ='{}'""".format(query,
                                                                  product_id))
        elif self.location_id:
            self.env.cr.execute(
                """{} where stock_move.location_id ='{}'""".format(query,
                                                                   location_id))
        elif self.partner_id:
            self.env.cr.execute(
                """{} where stock_picking.partner_id ='{}'""".format(query,
                                                                     partner_id))
        elif self.company_id:
            self.env.cr.execute(
                """{} where stock_picking.company_id ='{}'""".format(query,
                                                                     company_id))
        else:
            self.env.cr.execute("""{}""".format(query))
        stock_picking = self.env.cr.dictfetchall()
        data = {
            'product_name': self.product_id.product_tmpl_id.name,
            'location': self.location_id.complete_name,
            'Product Category': self.product_category_id.display_name,
            'company_name': self.company_id.name,
            'company_street': self.company_id.street,
            'state': self.company_id.state_id.name,
            'country': self.company_id.country_id.name,
            'company_email': self.company_id.email,
            'stock_picking': stock_picking,
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.transfer.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Stock Transfer Report'}}

    def get_xlsx_report(self, data, response):
        """ Function to print excel file.Customizing Excel file and
            adding data
            :param data :Dictionary contains results
            :param response : Response from the controller"""
        state = {'draft': 'Draft', 'waiting': 'Waiting Another Operation',
                 'confirmed': 'Waiting', 'assigned': 'Ready', 'done': 'Done',
                 'cancel': 'Cancelled'}
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 10, 24)
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'align': 'center'})
        sheet.merge_range('B2:I3', 'STOCK TRANSFER REPORT', head)
        sheet.merge_range('D4:F4', data['company_name'], txt)
        sheet.write('A8', 'SL No.', txt)
        sheet.write('B8', 'Reference', txt)
        sheet.write('C8', 'Product', txt)
        sheet.write('D8', 'scheduled Date', txt)
        sheet.write('E8', 'Deadline', txt)
        sheet.write('F8', 'Effective Date', txt)
        sheet.write('G8', 'Source Document', txt)
        sheet.write('H8', 'Location', txt)
        sheet.write('I8', 'Operation Type', txt)
        sheet.write('J8', 'Company Name', txt)
        sheet.write('K8', 'Status', txt)
        records = data['stock_picking']
        row = 9
        flag = 1
        for record in records:
            sheet.write(row, 0, flag, txt)
            sheet.write(row, 1, record['picking_name'], txt)
            sheet.write(row, 2, record['product_name'], txt)
            sheet.write(row, 3, record['scheduled_date'], txt)
            sheet.write(row, 4, record['date_deadline'], txt)
            sheet.write(row, 5, record['date_done'], txt)
            sheet.write(row, 6, record['origin'], txt)
            sheet.write(row, 7, record['complete_name'], txt)
            sheet.write(row, 8, record['display_name'], txt)
            sheet.write(row, 9, record['company_name'], txt)
            sheet.write(row, 10, state[record['state']], txt)
            flag += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
