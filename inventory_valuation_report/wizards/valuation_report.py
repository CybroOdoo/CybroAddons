# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sumith Sivan(<https://www.cybrosys.com>)
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
################################################################################
import io
import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class WizardReport(models.TransientModel):
    """Valuation report xlsx template """
    _name = 'valuation.report'

    company_id = fields.Many2one("res.company", sting="Company", required=True)
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouse",
                                     required=True)

    product_ids = fields.Many2many("product.product",
                                   help="Select the products")
    category_ids = fields.Many2many("product.category")
    filter_by = fields.Selection(
        [('product', 'Product'), ('category', 'Category')], string='Filter By')
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date", )
    summary = fields.Boolean(string="Summary", help="Print Summary Report")

    @api.onchange('company_id')
    def _compute_warehouse(self):
        if self.company_id:
            self.warehouse_ids = self.env['stock.warehouse'].search([
                ('company_id', '=', self.company_id.id)
            ]).ids
        else:
            self.warehouse_ids = False
        return {'domain': {
            'warehouse_ids': [('company_id', '=', self.company_id.id)]}}

    def action_btn_pdf(self):
        """Function to print pdf report"""
        product = self.env['product.product'].search(
            [('detailed_type', '=', 'product')])
        default_code = []
        product_ids = []
        category_ids = []
        warehouse = [rec.name for rec in self.warehouse_ids]

        if self.filter_by == "product":
            default_code = [rec.default_code for rec in self.product_ids]
            product_ids = [int(rec.id) for rec in self.product_ids]

        if self.filter_by == "category":
            category_ids = [int(rec.id) for rec in self.category_ids]
        data = {
            'from_date': self.start_date,
            'end_date': self.end_date,
            'my_company': self.company_id.name,
            'my_company_id': self.company_id.id,
            'currency': self.company_id.currency_id.name,
            'warehouse': warehouse,
            'filter_by': self.filter_by,
            'products': product_ids,
            'default_code': default_code,
            'categories': category_ids,
            'summary': self.summary,
            'all_product': product,

        }
        return self.env.ref(
            'inventory_valuation_report.action_report_valuation_report').report_action(
            self,
            data=data)

    def action_btn_xlsx(self):
        """Function to print xlsx report"""
        if self.warehouse_ids:
            warehouse_names = [rec.name for rec in self.warehouse_ids]
            warehouse = ', '.join(warehouse_names)
        if str(self.start_date) > str(self.end_date):
            raise ValidationError('Start Date must be less than End Date')

        query = """select product_product.id as product_id,product_template.default_code as default_code ,                  
        product_template.name->>'en_US' as name, product_category.name as category from product_template join               
        product_product on product_product.product_tmpl_id = product_template.id join product_category on                   
        product_template.categ_id = product_category.id """

        def get_data(res):
            product_id = [rec['product_id'] for rec in res]

            for i in range(len(res)):
                product = self.env['product.product'].browse(product_id[i])
                purchase_count = self.env['purchase.order.line'].search(
                    [('product_id', '=', product_id[i])])
                valuation = self.env['stock.valuation.layer'].search(
                    [('product_id', '=', product_id[i])],
                    order="create_date desc", limit=1)
                internal_locations = self.env['stock.location'].search(
                    [('usage', '=', 'internal')])
                internal_qty = 0

                for quant in internal_locations:
                    tracking = product.tracking
                    if tracking == 'lot':
                        lot_qty = self.env['stock.lot'].search(
                            [('product_id', '=', product_id[i])])
                        lot_qty_count = self.env['stock.quant'].search([
                            ('product_id', '=', product_id[i]),
                            ('lot_id', 'in', lot_qty.ids),
                            ('location_id', '=', quant.id)
                        ])
                        internal_qty += sum(
                            lot_qty_count.mapped('available_quantity'))
                    else:
                        internal_stock_quant = self.env['stock.quant'].search(
                            [('location_id', '=', quant.id),
                             ('product_id', '=', product_id[i])])
                        internal_qty += internal_stock_quant.available_quantity

                adjustment_rec = self.env['stock.quant'].search(
                    [('product_id', '=', product_id[i])],
                    order="create_date desc", limit=1)
                adjustment = adjustment_rec.inventory_diff_quantity
                res[i][
                    'costing_method'] = product.categ_id.property_cost_method
                res[i]['standard_price'] = product.standard_price
                res[i]['sale_qty'] = product.sales_count
                res[i]['received_qty'] = sum(
                    purchase_count.mapped('product_uom_qty'))
                res[i]['beginning'] = res[i]['received_qty'] - res[i][
                    'sale_qty']
                res[i]['valuation'] = valuation.value
                res[i]['internal'] = internal_qty
                res[i]['adjustment'] = adjustment
            return res

        product_ids = [rec.id for rec in self.product_ids]
        category_ids = [rec.id for rec in self.category_ids]

        if self.company_id:
            query += f""" join res_company on res_company.id=product_template.company_id where res_company.id = '{self.company_id.id}'"""

        if self.start_date:
            query += f""" and product_product.create_date >= '{self.start_date}'"""

        if self.end_date:
            query += f""" and product_product.create_date <= '{self.end_date}'"""

        product = tuple(product_ids)
        categories = tuple(category_ids)

        if self.filter_by == 'product':
            if len(product) == 1:
                query += f""" and product_product.id = {product[0]} """
            elif len(product) > 1:
                query += f""" and product_product.id in {product} """
            else:
                raise ValidationError('No Product Found')
        if self.filter_by == 'category':
            if len(categories) == 1:
                query += f""" and product_category.id = {categories[0]}"""

            elif len(categories) > 1:
                query += f""" and product_category.id in {categories} """
            else:
                raise ValidationError('No Category Found')

        self.env.cr.execute(query)
        record = self.env.cr.dictfetchall()
        result = get_data(record)
        data = {
            'from_date': self.start_date,
            'end_date': self.end_date,
            'my_company': self.company_id.name,
            'currency': self.company_id.currency_id.name,
            'warehouse': warehouse,
            'summary': self.summary,
            'excel_result': result
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'valuation.report',
                'output_format': 'xlsx',
                'options': json.dumps(data, default=date_utils.json_default),
                'report_name': 'Excel Report Name',
            }
        }

    def get_xlsx_report(self, data, response):
        """xlsx report template"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'align': 'center', 'font_size': '10px'})
        columns = ['C:C', 'B:B', 'D:D', 'E:E', 'F:F', 'G:G', 'H:H', 'I:I',
                   'J:J', 'L:L', 'M:M']
        for column in columns:
            sheet.set_column(column, 20)
        if data['summary']:
            sheet.merge_range('B2:I3', 'Summary Valuation REPORT', head)
            if data['from_date']:
                sheet.write('B5', 'Start Date', cell_format)
                sheet.write('B6', data['from_date'], txt)
            if data['end_date']:
                sheet.write('D5', 'End Date', cell_format)
                sheet.write('D6', data['end_date'], txt)
            if data['my_company']:
                sheet.write('F5', 'Company', cell_format)
                sheet.write('F6', data['my_company'], txt)
            if data['warehouse']:
                sheet.merge_range('G5:H5', 'Warehouse(s)', cell_format)
                sheet.merge_range('G6:H6', data['warehouse'], txt)
            if data['currency']:
                sheet.write('I5', 'Currency', cell_format)
                sheet.write('I6', data['currency'], txt)
            sheet.write('B8', 'Sl.No', txt)
            sheet.write('C8', 'Category', txt)
            sheet.write('D8', 'Costing Method', txt)
            sheet.write('E8', 'Cost Price', txt)
            sheet.write('F8', 'Beginning', txt)
            sheet.write('G8', 'Internal', txt)
            sheet.write('H8', 'Received', txt)
            sheet.write('I8', 'Sales', txt)
            sheet.write('J8', 'Adjustment', txt)
            sheet.write('K8', 'Ending', txt)
            sheet.write('L8', 'Valuation', txt)

            row_number = 9
            column_number = 1
            count = 1
            for i in data['excel_result']:
                sheet.write(row_number, column_number, count, txt)
                sheet.write(row_number, column_number + 1, i['category'], txt)
                sheet.write(row_number, column_number + 2, i['costing_method'],
                            txt)
                sheet.write(row_number, column_number + 3, i['standard_price'],
                            txt)
                sheet.write(row_number, column_number + 4,
                            i['received_qty'] - i['sale_qty'], txt)
                sheet.write(row_number, column_number + 5, i['internal'], txt)
                sheet.write(row_number, column_number + 6, i['received_qty'],
                            txt)
                sheet.write(row_number, column_number + 7, i['sale_qty'], txt)
                sheet.write(row_number, column_number + 8, i['adjustment'],
                            txt)
                sheet.write(row_number, column_number + 9,
                            i['beginning'] + i['received_qty'] - i['sale_qty'] +
                            i['adjustment'], txt)
                sheet.write(row_number, column_number + 10, i['valuation'],
                            txt)

                row_number += 1
                count += 1
            workbook.close()
            output.seek(0)
            response.stream.write(output.read())
            output.close()
        else:
            sheet.merge_range('B2:I3', 'Inventory Valuation REPORT', head)
            if data['from_date']:
                sheet.write('B5', 'Start Date', cell_format)
                sheet.write('B6', data['from_date'], txt)
            if data['end_date']:
                sheet.write('D5', 'End Date', cell_format)
                sheet.write('D6', data['end_date'], txt)
            if data['my_company']:
                sheet.write('F5', 'Company', cell_format)
                sheet.write('F6', data['my_company'], txt)
            if data['warehouse']:
                sheet.merge_range('G5:H5', 'Warehouse(s)', cell_format)
                sheet.merge_range('G6:H6', data['warehouse'], txt)
            if data['currency']:
                sheet.write('I5', 'Currency', cell_format)
                sheet.write('I6', data['currency'], txt)

            sheet.write('B9', 'Sl.No', txt)
            sheet.write('C9', 'Default Code', txt)
            sheet.write('D9', 'Name', txt)
            sheet.write('E9', 'Category', txt)
            sheet.write('F9', 'Costing Method', txt)
            sheet.write('G9', 'Cost Price', txt)
            sheet.write('H9', 'Beginning', txt)
            sheet.write('I9', 'Internal', txt)
            sheet.write('J9', 'Received', txt)
            sheet.write('K9', 'Sales', txt)
            sheet.write('L9', 'Adjustment', txt)
            sheet.write('M9', 'Ending', txt)
            sheet.write('N9', 'Valuation', txt)

            row_number = 10
            column_number = 1
            count = 1
            for i in data['excel_result']:
                sheet.write(row_number, column_number, count, txt)
                sheet.write(row_number, column_number + 1, i['default_code'],
                            txt)
                sheet.write(row_number, column_number + 2, i['name'], txt)
                sheet.write(row_number, column_number + 3, i['category'], txt)
                sheet.write(row_number, column_number + 4, i['costing_method'],
                            txt)
                sheet.write(row_number, column_number + 5, i['standard_price'],
                            txt)
                sheet.write(row_number, column_number + 6,
                            i['received_qty'] - i['sale_qty'], txt)
                sheet.write(row_number, column_number + 7, i['internal'], txt)
                sheet.write(row_number, column_number + 8, i['received_qty'],
                            txt)
                sheet.write(row_number, column_number + 9, i['sale_qty'], txt)
                sheet.write(row_number, column_number + 10, i['adjustment'],
                            txt)
                sheet.write(row_number, column_number + 11,
                            i['beginning'] + i['received_qty'] - i['sale_qty'] +
                            i['adjustment'], txt)
                sheet.write(row_number, column_number + 12, i['valuation'],
                            txt)
                row_number += 1
                count += 1
            workbook.close()
            output.seek(0)
            response.stream.write(output.read())
            output.close()
