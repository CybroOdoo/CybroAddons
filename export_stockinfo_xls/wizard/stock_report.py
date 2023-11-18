# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from datetime import datetime
import datetime
import pytz
from odoo import fields, models
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class StockReport(models.TransientModel):
    """Create a new model named 'stock_report' to implement a wizard.
    This wizard will allow users to select warehouses and categories for
    printing purposes."""

    _name = "stock.xls.report"
    _description = "Current Stock History"

    warehouse_ids = fields.Many2many('stock.warehouse',
                                     string='Warehouse',
                                     required=True)
    category_ids = fields.Many2many('product.category',
                                    string='Category')

    def export_xls(self):
        """Function to retrieve and open an XLS report record."""
        data = {
            'ids': self.ids,
            'model': self._name,
            'warehouse': self.warehouse_ids.ids,
            'category': self.category_ids.ids,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'stock.xls.report',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Current Stock History',
                     },
            'report_type': 'stock_xlsx'
        }

    def get_warehouse(self, data):
        """Function to retrieve all warehouses."""
        warehouse = self.env['stock.warehouse'].search(
            [('id', 'in', data.warehouse_ids.mapped('id'))])
        warehouse_name = [rec.name for rec in warehouse]
        warehouse_id = [rec.id for rec in warehouse]
        return warehouse_name, warehouse_id

    def get_lines(self, data, warehouse_ids):
        """Functions for retrieving data for an XLS report"""
        lines = []
        if data.mapped('id'):
            category_products = self.env['product.product'].search(
                [('categ_id', 'in', data.mapped('id'))])
        else:
            category_products = self.env['product.product'].search([])
        product_ids = tuple([pro_id.id for pro_id in category_products])
        sale_query = """
               SELECT sum(s_o_l.product_uom_qty) AS product_uom_qty, s_o_l.product_id FROM sale_order_line AS s_o_l
               JOIN sale_order AS s_o ON s_o_l.order_id = s_o.id
               WHERE s_o.state IN ('sale','done')
               AND s_o.warehouse_id = %s
               AND s_o_l.product_id in %s group by s_o_l.product_id"""
        purchase_query = """
               SELECT sum(p_o_l.product_qty) AS product_qty, p_o_l.product_id FROM purchase_order_line AS p_o_l
               JOIN purchase_order AS p_o ON p_o_l.order_id = p_o.id
               INNER JOIN stock_picking_type AS s_p_t ON p_o.picking_type_id = s_p_t.id
               WHERE p_o.state IN ('purchase','done')
               AND s_p_t.warehouse_id = %s AND p_o_l.product_id in %s group by p_o_l.product_id"""
        params = warehouse_ids, product_ids if product_ids else (0, 0)
        self._cr.execute(sale_query, params)
        self._cr.execute(purchase_query, params)
        for rec in category_products:
            sale_value = 0
            purchase_value = 0
            for sale_product in self._cr.dictfetchall():
                if sale_product['product_id'] == rec.id:
                    sale_value = sale_product['product_uom_qty']
            for purchase_product in self._cr.dictfetchall():
                if purchase_product['product_id'] == rec.id:
                    purchase_value = purchase_product['product_qty']
            virtual_available = rec.with_context(
                {'warehouse': warehouse_ids}).virtual_available
            outgoing_qty = rec.with_context(
                {'warehouse': warehouse_ids}).outgoing_qty
            incoming_qty = rec.with_context(
                {'warehouse': warehouse_ids}).incoming_qty
            available_qty = virtual_available + outgoing_qty - incoming_qty
            vals = {
                'sku': rec.default_code,
                'name': rec.name,
                'category': rec.categ_id.name,
                'cost_price': rec.standard_price,
                'available': available_qty,
                'virtual': virtual_available,
                'incoming': incoming_qty,
                'outgoing': outgoing_qty,
                'net_on_hand': rec.with_context(
                    {'warehouse': warehouse_ids}).qty_available,
                'total_value': available_qty * rec.standard_price,
                'sale_value': sale_value,
                'purchase_value': purchase_value,
            }
            lines.append(vals)
        return lines

    def get_xlsx_report(self, data, response):
        """Function for designing an XLS report including warehouse and
        category data."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Stock Info')
        format0 = workbook.add_format(
            {'font_size': 20, 'align': 'center', 'bold': True})
        format1 = workbook.add_format(
            {'font_size': 14, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bold': True})
        format21 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format(
            {'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format(
            {'font_size': 12, 'align': 'left', 'bold': True})
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheet.merge_range(1, 7, 2, 10, 'Product Stock Info', format0)
        sheet.merge_range(3, 7, 3, 10, self.env.user.company_id.name, format11)
        category_object = []
        if self.browse(data['ids']).category_ids.mapped('id'):
            for res in self.browse(data['ids']).category_ids.mapped('id'):
                category_object.append(
                    self.env['product.category'].browse(res).name)
            category = ', '.join(category_object)
            sheet.merge_range(4, 0, 4, 1, 'Category(s) : ', format4)
            sheet.merge_range(4, 2, 4, 3 + len(
                self.browse(data['ids']).category_ids.mapped('id')), category,
                              format4)
        sheet.merge_range(5, 0, 5, 1, 'Warehouse(s) : ', format4)
        ware_house = ', '.join(self.get_warehouse(self.browse(data['ids']))[0])
        sheet.merge_range(5, 2, 5, 3 + len(
            self.get_warehouse(self.browse(data['ids']))[0]), ware_house,
                          format4)
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else 'UTC')
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        sheet.merge_range('A8:G8', 'Report Date: ' + str(
            times.strftime("%Y-%m-%d %H:%M %p")), format1)
        sheet.merge_range(7, 7, 7, len(
            self.get_warehouse(self.browse(data['ids']))[0]) * 11 + 6,
                          'Warehouses', format1)
        sheet.merge_range('A9:G9', 'Product Information', format11)
        w_col_no = 6
        w_col_no1 = 7
        for record in self.get_warehouse(self.browse(data['ids']))[0]:
            w_col_no = w_col_no + 11
            sheet.merge_range(8, w_col_no1, 8, w_col_no, record, format11)
            w_col_no1 = w_col_no1 + 11
        sheet.write(9, 0, 'SKU', format21)
        sheet.merge_range(9, 1, 9, 3, 'Name', format21)
        sheet.merge_range(9, 4, 9, 5, 'Category', format21)
        sheet.write(9, 6, 'Cost Price', format21)
        p_col_no1 = 7
        for record in self.get_warehouse(self.browse(data['ids']))[0]:
            w_col_no = w_col_no + 11
            sheet.merge_range(8, w_col_no1, 8, w_col_no, record, format11)
            sheet.write(9, p_col_no1, 'Available', format21)
            sheet.write(9, p_col_no1 + 1, 'Virtual', format21)
            sheet.write(9, p_col_no1 + 2, 'Incoming', format21)
            sheet.write(9, p_col_no1 + 3, 'Outgoing', format21)
            sheet.merge_range(9, p_col_no1 + 4, 9, p_col_no1 + 5, 'Net On Hand',
                              format21)
            sheet.merge_range(9, p_col_no1 + 6, 9, p_col_no1 + 7, 'Total Sold',
                              format21)
            sheet.merge_range(9, p_col_no1 + 8, 9, p_col_no1 + 9,
                              'Total Purchased', format21)
            sheet.write(9, p_col_no1 + 10, 'Valuation', format21)
            p_col_no1 = p_col_no1 + 11
        prod_row = 10
        prod_col = 0
        for record in self.get_warehouse(self.browse(data['ids']))[1]:
            get_line = self.get_lines(self.browse(data['ids']).category_ids,
                                      record)
            for each in get_line:
                sheet.write(prod_row, prod_col, each['sku'], font_size_8)
                sheet.merge_range(prod_row, prod_col + 1, prod_row,
                                  prod_col + 3, each['name'], font_size_8_l)
                sheet.merge_range(prod_row, prod_col + 4, prod_row,
                                  prod_col + 5, each['category'], font_size_8_l)
                sheet.write(prod_row, prod_col + 6, each['cost_price'],
                            font_size_8_r)
                prod_row = prod_row + 1
            break
        prod_row = 10
        prod_col = 7
        for record in self.get_warehouse(self.browse(data['ids']))[1]:
            get_line = self.get_lines(self.browse(data['ids']).category_ids,
                                      record)
            for each in get_line:
                if each['available'] < 0:
                    sheet.write(prod_row, prod_col, each['available'], red_mark)
                else:
                    sheet.write(prod_row, prod_col, each['available'],
                                font_size_8)
                if each['virtual'] < 0:
                    sheet.write(prod_row, prod_col + 1, each['virtual'],
                                red_mark)
                else:
                    sheet.write(prod_row, prod_col + 1, each['virtual'],
                                font_size_8)
                if each['incoming'] < 0:
                    sheet.write(prod_row, prod_col + 2, each['incoming'],
                                red_mark)
                else:
                    sheet.write(prod_row, prod_col + 2, each['incoming'],
                                font_size_8)
                if each['outgoing'] < 0:
                    sheet.write(prod_row, prod_col + 3, each['outgoing'],
                                red_mark)
                else:
                    sheet.write(prod_row, prod_col + 3, each['outgoing'],
                                font_size_8)
                if each['net_on_hand'] < 0:
                    sheet.merge_range(prod_row, prod_col + 4, prod_row,
                                      prod_col + 5, each['net_on_hand'],
                                      red_mark)
                else:
                    sheet.merge_range(prod_row, prod_col + 4, prod_row,
                                      prod_col + 5, each['net_on_hand'],
                                      font_size_8)
                    if each['sale_value'] < 0:
                        sheet.merge_range(prod_row, prod_col + 6, prod_row,
                                          prod_col + 7, each['sale_value'],
                                          red_mark)
                    else:
                        sheet.merge_range(prod_row, prod_col + 6, prod_row,
                                          prod_col + 7, each['sale_value'],
                                          font_size_8)
                if each['purchase_value'] < 0:
                    sheet.merge_range(prod_row, prod_col + 8, prod_row,
                                      prod_col + 9, each['purchase_value'],
                                      red_mark)
                else:
                    sheet.merge_range(prod_row, prod_col + 8, prod_row,
                                      prod_col + 9, each['purchase_value'],
                                      font_size_8)
                if each['total_value'] < 0:
                    sheet.write(prod_row, prod_col + 10, each['total_value'],
                                red_mark)
                else:
                    sheet.write(prod_row, prod_col + 10, each['total_value'],
                                font_size_8_r)
                prod_row = prod_row + 1
            prod_row = 10
            prod_col = prod_col + 11
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
