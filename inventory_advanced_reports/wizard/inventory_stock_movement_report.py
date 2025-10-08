# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import io
import json
from odoo import fields, models
from odoo.exceptions import ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class InventoryStockMovementReport(models.TransientModel):
    """This model is for creating a wizard for inventory Over Stock report."""
    _name = 'inventory.stock.movement.report'
    _description = 'Inventory Stock Movement Report'

    start_date = fields.Date('Start Date',
                             default=lambda self: fields.Date.today(),
                             help="Start date to analyze the report")
    end_date = fields.Date('End Date',
                           default=lambda self: fields.Date.today(),
                           help="End date to analyse the report")
    warehouse_ids = fields.Many2many(
        "stock.warehouse", string="Warehouses",
        help="Select the warehouses to generate the report")
    product_ids = fields.Many2many(
        "product.product", string="Products",
        help="Select the products you want to generate the report for")
    category_ids = fields.Many2many(
        "product.category", string="Product categories",
        help="Select the product categories you want to generate the report for"
    )
    company_ids = fields.Many2many(
        "res.company", string="Company", default=lambda self: self.env.company,
        help="Select the companies you want to generate the report for")
    report_up_to_certain_date = fields.Boolean(string="Date upto")
    up_to_certain_date = fields.Date(string="Movements Upto")

    def get_report_data(self):
        """Function for returning the values for printing"""
        query = """
                        SELECT
                            pp.id as product_id,
                            CASE
                            WHEN pp.default_code IS NOT NULL 
                                THEN CONCAT(pp.default_code, ' - ', 
                                pt.name->>'en_US')
                            ELSE
                                pt.name->>'en_US'
                            END AS product_code_and_name, 
                            pc.complete_name AS category_name,
                            company.name AS company_name,                       
                """
        if self.report_up_to_certain_date:
            query += """
                    SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'inventory' 
                    THEN sm.product_uom_qty ELSE 0 END) AS opening_stock,
                    (SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END)) AS closing_stock,
                    SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'customer' 
                    THEN sm.product_uom_qty ELSE 0 END) AS sales,
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'customer' 
                    THEN sm.product_uom_qty ELSE 0 END) AS sales_return,
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'supplier' 
                    THEN sm.product_uom_qty ELSE 0 END) AS purchase,
                    SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'supplier' 
                    THEN sm.product_uom_qty ELSE 0 END) AS purchase_return,
                    SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) AS internal_in,
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) AS internal_out,
                    SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'inventory' 
                    THEN sm.product_uom_qty ELSE 0 END) AS adj_in,
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'inventory' 
                    THEN sm.product_uom_qty ELSE 0 END) AS adj_out,
                    SUM(CASE WHEN sm.date <= %s 
                    AND sld_dest.usage = 'production' 
                    THEN sm.product_uom_qty ELSE 0 END) AS production_in,
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'production' 
                    THEN sm.product_uom_qty ELSE 0 END) AS production_out,
                    SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'transit' 
                    THEN sm.product_uom_qty ELSE 0 END) AS transit_in,
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'transit' 
                    THEN sm.product_uom_qty ELSE 0 END) AS transit_out
                    """
            params = [self.up_to_certain_date] * 15
        else:
            query += """
                        (SUM(CASE WHEN sm.date <= %s 
                        AND sld_dest.usage = 'internal' 
                        THEN sm.product_uom_qty ELSE 0 END) -
                        SUM(CASE WHEN sm.date <= %s 
                        AND sld_src.usage = 'internal' 
                        THEN sm.product_uom_qty ELSE 0 END)) AS opening_stock,
                        (SUM(CASE WHEN sm.date <= %s 
                        AND sld_dest.usage = 'internal' 
                        THEN sm.product_uom_qty ELSE 0 END) -
                        SUM(CASE WHEN sm.date <= %s 
                        AND sld_src.usage = 'internal' 
                        THEN sm.product_uom_qty ELSE 0 END)) AS closing_stock,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_dest.usage = 'customer' 
                        THEN sm.product_uom_qty ELSE 0 END) AS sales,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_src.usage = 'customer' 
                        THEN sm.product_uom_qty ELSE 0 END) AS sales_return,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_src.usage = 'supplier' 
                        THEN sm.product_uom_qty ELSE 0 END) AS purchase,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_dest.usage = 'supplier' 
                        THEN sm.product_uom_qty ELSE 0 END) AS purchase_return,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_dest.usage = 'internal' 
                        THEN sm.product_uom_qty ELSE 0 END) AS internal_in,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_src.usage = 'internal' 
                        THEN sm.product_uom_qty ELSE 0 END) AS internal_out,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_dest.usage = 'inventory' 
                        THEN sm.product_uom_qty ELSE 0 END) AS adj_in,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_src.usage = 'inventory' 
                        THEN sm.product_uom_qty ELSE 0 END) AS adj_out,
                        SUM(CASE WHEN sm.date BETWEEN %s 
                        AND %s AND sld_dest.usage = 'production' 
                        THEN sm.product_uom_qty ELSE 0 END) AS production_in,
                        SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                        AND sld_src.usage = 'production' 
                        THEN sm.product_uom_qty ELSE 0 END) AS production_out,
                        SUM(CASE WHEN sm.date BETWEEN %s 
                        AND %s AND sld_dest.usage = 'transit' 
                        THEN sm.product_uom_qty ELSE 0 END) AS transit_in,
                        SUM(CASE WHEN sm.date BETWEEN %s 
                        AND %s AND sld_src.usage = 'transit' 
                        THEN sm.product_uom_qty ELSE 0 END) AS transit_out
                    """
            params = [self.start_date, self.start_date, self.end_date, self.end_date] + [self.start_date, self.end_date] * 12
        query += """
                    FROM stock_move sm
                    INNER JOIN product_product pp ON pp.id = sm.product_id
                    INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    INNER JOIN res_company company ON company.id = sm.company_id
                    INNER JOIN product_category pc ON pc.id = pt.categ_id   
                """
        query += """
                    LEFT JOIN stock_location sld_dest 
                    ON sm.location_dest_id = sld_dest.id
                    LEFT JOIN stock_location sld_src 
                    ON sm.location_id = sld_src.id
                    LEFT JOIN
                    stock_warehouse sw_dest ON sld_dest.warehouse_id = sw_dest.id
                    LEFT JOIN
                    stock_warehouse sw_src ON sld_src.warehouse_id = sw_src.id
                    WHERE
                sm.state = 'done'
                        """
        if self.product_ids:
            product_ids = [product_id.id for product_id in self.product_ids]
            query += "AND pp.id = ANY(%s)"
            params.append(product_ids)
        if self.category_ids:
            category_ids = [category.id for category in self.category_ids]
            query += "AND pt.categ_id = ANY(%s)"
            params.append(category_ids)
        if self.company_ids:
            company_ids = [company.id for company in self.company_ids]
            query += " AND sm.company_id = ANY(%s)"
            params.append(company_ids)
        if self.warehouse_ids:
            warehouse_ids = [warehouse.id for warehouse in self.warehouse_ids]
            query += " AND (COALESCE(sw_dest.id, sw_src.id) = ANY(%s))"
            params.append(warehouse_ids)
        query += """
            GROUP BY pp.id,pt.name,pc.complete_name,company.name
        """
        self.env.cr.execute(query, params)
        result_data = self.env.cr.dictfetchall()
        if result_data:
            data = {
                'data': result_data,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'up_to_certain_date': self.up_to_certain_date
            }
            return data
        else:
            raise ValidationError("No records found for the given criteria!")

    def action_pdf(self):
        """Function for printing the pdf report"""
        data = {
            'model_id': self.id,
            'product_ids': self.product_ids.ids,
            'category_ids': self.category_ids.ids,
            'company_ids': self.company_ids.ids,
            'warehouse_ids': self.warehouse_ids.ids,
            'start_date': self.start_date,
            "end_date": self.end_date,
            "report_up_to_certain_date": self.report_up_to_certain_date,
            "up_to_certain_date": self.up_to_certain_date
        }
        return (
            self.env.ref(
                'inventory_advanced_reports.'
                'report_inventory_stock_movement_action')
            .report_action(None, data=data))

    def action_excel(self):
        """This function is for printing excel report"""
        data = self.get_report_data()
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'inventory.stock.movement.report',
                     'options': json.dumps
                     (data, default=fields.date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Excel format to print the data in Excel sheet"""
        datas = data['data']
        start_date = data['start_date']
        end_date = data['end_date']
        up_to_certain_date = data['up_to_certain_date']
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'left'})
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1,
             'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1,
             'align': 'left'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        bold_format = workbook.add_format(
            {'bold': True, 'font_size': '10px', 'align': 'left'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})
        if start_date and end_date and not up_to_certain_date:
            sheet.write('A6', 'From Date: ', bold_format)
            sheet.write('B6', start_date, txt)
            sheet.write('A7', 'To Date: ', bold_format)
            sheet.write('B7', end_date, txt)
        if up_to_certain_date:
            sheet.write('A7', 'Stock Movements Up To: ', bold_format)
            sheet.write('B7', up_to_certain_date, txt)
        sheet.merge_range('E2:K3', 'Inventory Stock Movement Report', head)
        headers = ['Company', 'Product', 'Category', 'Opening Stock', 'Sales',
                   'Sales Return', 'Purchase', 'Purchase Return', 'Internal In',
                   'Internal Out', 'Adjustment In', 'Adjustment Out',
                   'Production In', 'Production Out', 'Transit In',
                   'Transit Out', 'Closing Stock']
        for col, header in enumerate(headers):
            sheet.write(8, col, header, header_style)
        sheet.set_column('A:A', 23, cell_format)
        sheet.set_column('B:B', 27, cell_format)
        sheet.set_column('C:C', 25, cell_format)
        sheet.set_column('D:D', 13, cell_format)
        sheet.set_column('E:E', 13, cell_format)
        sheet.set_column('F:G', 15, cell_format)
        sheet.set_column('H:I', 15, cell_format)
        sheet.set_column('J:K', 15, cell_format)
        sheet.set_column('L:M', 15, cell_format)
        sheet.set_column('N:O', 15, cell_format)
        sheet.set_column('P:Q', 15, cell_format)
        row = 9
        number = 1
        for val in datas:
            sheet.write(row, 0, val['company_name'], text_style)
            sheet.write(row, 1, val['product_code_and_name'], text_style)
            sheet.write(row, 2, val['category_name'], text_style)
            sheet.write(row, 3, val['opening_stock'], text_style)
            sheet.write(row, 4, val['sales'], text_style)
            sheet.write(row, 5, val['sales_return'], text_style)
            sheet.write(row, 6, val['purchase'], text_style)
            sheet.write(row, 7, val['purchase_return'], text_style)
            sheet.write(row, 8, val['internal_in'], text_style)
            sheet.write(row, 9, val['internal_out'], text_style)
            sheet.write(row, 10, val['adj_in'], text_style)
            sheet.write(row, 11, val['adj_out'], text_style)
            sheet.write(row, 12, val['production_in'], text_style)
            sheet.write(row, 13, val['production_out'], text_style)
            sheet.write(row, 14, val['transit_in'], text_style)
            sheet.write(row, 15, val['transit_out'], text_style)
            sheet.write(row, 16, val['closing_stock'], text_style)
            row += 1
            number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
