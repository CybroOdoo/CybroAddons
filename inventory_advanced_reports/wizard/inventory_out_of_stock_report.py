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
from odoo import fields, models, _
from odoo.exceptions import ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class InventoryOutOfStockReport(models.TransientModel):
    """This model is for creating a wizard for inventory turnover report."""
    _name = 'inventory.out.of.stock.report'
    _description = 'Inventory Out of Stock Report'

    start_date = fields.Date('Start Date',
                             help="Start date to analyse the report",
                             required=True)
    end_date = fields.Date('End Date', help="End date to analyse the report",
                           required=True)
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
    inventory_for_next_x_days = fields.Integer(
        string="Inventory For Next X Days",
        help="Select next number of days for the inventory")

    def get_report_data(self):
        """Function for returning data to print"""
        query = """
            SELECT
                product_id,
                product_code_and_name,
                category_id,
                category_name,
                company_id,
                current_stock,
                warehouse_id,
                incoming_quantity,
                outgoing_quantity,
                virtual_stock,
                sales,
                ads,
                advance_stock_days,
                ROUND(advance_stock_days * ads, 0) AS demanded_quantity,
                ROUND(CASE
                    WHEN ads = 0 THEN virtual_stock / 0.001
                    ELSE virtual_stock / ads
                END,0) AS in_stock_days,
                ROUND(CASE
                    WHEN ads = 0 THEN GREATEST(advance_stock_days - ROUND(virtual_stock / 0.001, 2), 0)
                    ELSE GREATEST(advance_stock_days - ROUND(virtual_stock / ads, 2), 0)
                END ,0) AS out_of_stock_days,
                ROUND(
                    CASE
                        WHEN advance_stock_days = 0 THEN 0
                        ELSE
                            CASE
                                WHEN ads = 0 THEN GREATEST(advance_stock_days - ROUND(virtual_stock / 0.001, 2), 0)
                                ELSE GREATEST(advance_stock_days - ROUND(virtual_stock / ads, 2), 0)
                            END
                    END, 2
                ) AS out_of_stock_ratio,
                ROUND(
                    CASE
                        WHEN ads = 0 THEN GREATEST(advance_stock_days - ROUND(virtual_stock / 0.001, 2), 0)
                        ELSE GREATEST(advance_stock_days - ROUND(virtual_stock / ads, 2), 0)
                    END * ads, 0
                ) AS out_of_stock_qty,
                ROUND(
                    CASE
                        WHEN virtual_stock = 0 THEN 0 
                        ELSE sales / virtual_stock
                    END, 2
                ) AS turnover_ratio,
                CASE
                    WHEN
                        CASE
                            WHEN sales > 0 THEN ROUND((sales / NULLIF(virtual_stock, 0)), 2)
                            ELSE 0
                        END > 3 THEN 'Fast Moving'
                    WHEN
                        CASE
                            WHEN sales > 0 THEN ROUND((sales / NULLIF(virtual_stock, 0)), 2)
                            ELSE 0
                        END >= 1 AND
                        CASE
                            WHEN sales > 0 THEN ROUND((sales / NULLIF(virtual_stock, 0)), 2)
                            ELSE 0
                        END <= 3 THEN 'Slow Moving'
                    ELSE 'Non Moving'
                END AS fsn_classification
            FROM(
                SELECT 
                    CASE
                        WHEN pp.default_code IS NOT NULL 
                            THEN CONCAT(pp.default_code, ' - ', pt.name->>'en_US')
                        ELSE
                            pt.name->>'en_US'
                    END AS product_code_and_name,
                    company.id AS company_id,
                    company.name AS company_name,
                    sm.product_id AS product_id,
                    pc.id AS category_id,
                    pc.complete_name AS category_name,
                    COALESCE(sld_dest.warehouse_id, sld_src.warehouse_id) AS warehouse_id,
                    SUM(CASE
                        WHEN sld_dest.usage = 'internal' AND sm.state IN ('assigned', 'confirmed', 'waiting') 
                        THEN sm.product_uom_qty
                        ELSE 0
                    END) AS incoming_quantity,
                    SUM(CASE
                        WHEN sld_src.usage = 'internal' AND sm.state IN ('assigned', 'confirmed', 'waiting') 
                        THEN sm.product_uom_qty
                        ELSE 0
                    END) AS outgoing_quantity,
                    SUM(CASE
                        WHEN sld_dest.usage = 'internal' AND sm.state = 'done' 
                        THEN sm.product_uom_qty
                        ELSE 0
                    END) -
                    SUM(CASE
                        WHEN sld_src.usage = 'internal' AND sm.state = 'done' 
                        THEN sm.product_uom_qty
                        ELSE 0
                    END) AS current_stock,
                    SUM(CASE
                        WHEN sld_dest.usage = 'internal' AND sm.state = 'done' 
                        THEN sm.product_uom_qty
                        ELSE 0
                    END) -
                    SUM(CASE
                        WHEN sld_src.usage = 'internal' AND sm.state = 'done' 
                        THEN sm.product_uom_qty
                        ELSE 0
                    END)+
                    SUM(CASE
                        WHEN sld_dest.usage = 'internal' AND sm.state IN ('assigned', 'confirmed', 'waiting') 
                        THEN sm.product_uom_qty
                        ELSE 0
                    END) -
                    SUM(CASE
                        WHEN sld_src.usage = 'internal' AND sm.state IN ('assigned', 'confirmed', 'waiting') 
                        THEN sm.product_uom_qty
                        ELSE 0
                    END) AS virtual_stock,
                    SUM(CASE WHEN sm.date BETWEEN %s AND %s AND sld_dest.usage = 'customer' 
                        THEN sm.product_uom_qty ELSE 0 END) AS sales,
                    ROUND(SUM(CASE
                        WHEN sm.date BETWEEN %s AND %s AND sld_src.usage = 'internal' 
                        AND sm.state = 'done' THEN sm.product_uom_qty
                        ELSE 0
                    END) / ((date %s - date %s)+1), 2) AS ads,
                    %s AS advance_stock_days
                FROM stock_move sm
                INNER JOIN product_product pp ON pp.id = sm.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                INNER JOIN res_company company ON company.id = sm.company_id
                INNER JOIN product_category pc ON pc.id = pt.categ_id
                LEFT JOIN (
                    SELECT sm.id AS move_id, sld.usage, sw.id AS warehouse_id
                    FROM stock_location sld
                    INNER JOIN stock_move sm ON sld.id = sm.location_dest_id
                    LEFT JOIN stock_warehouse sw ON sld.warehouse_id = sw.id
                ) sld_dest ON sm.id = sld_dest.move_id
                LEFT JOIN (
                    SELECT sm.id AS move_id, sld.usage, sw.id AS warehouse_id
                    FROM stock_location sld
                    INNER JOIN stock_move sm ON sld.id = sm.location_id
                    LEFT JOIN stock_warehouse sw ON sld.warehouse_id = sw.id
                ) sld_src ON sm.id = sld_src.move_id
                WHERE pp.active = TRUE
                    AND pt.active = TRUE
                    AND pt.type = 'product'
        """
        params = [
            self.start_date, self.end_date,
            self.start_date, self.end_date,
            self.end_date, self.start_date,
            self.inventory_for_next_x_days
        ]
        if self.product_ids or self.category_ids:
            query += " AND ("
        if self.product_ids:
            product_ids = [product_id.id for product_id in self.product_ids]
            query += "pp.id = ANY(%s)"
            params.append(product_ids)
        if self.product_ids and self.category_ids:
            query += " OR "
        if self.category_ids:
            category_ids = [category.id for category in self.category_ids]
            params.append(category_ids)
            query += "(pt.categ_id = ANY(%s))"
        if self.product_ids or self.category_ids:
            query += ")"
        if self.company_ids:
            company_ids = [company.id for company in self.company_ids]
            query += " AND (sm.company_id = ANY(%s))"  # Specify the table alias
            params.append(company_ids)
        if self.warehouse_ids:
            warehouse_ids = [warehouse.id for warehouse in self.warehouse_ids]
            query += " AND (COALESCE(sld_dest.warehouse_id, sld_src.warehouse_id) = ANY(%s))"
            params.append(warehouse_ids)
        query += """ GROUP BY pp.id, pt.name, pc.id, company.id, sm.product_id, 
                        COALESCE(sld_dest.warehouse_id, sld_src.warehouse_id)
                    ) AS sub_query """
        self.env.cr.execute(query, tuple(params))
        result_data = self.env.cr.dictfetchall()
        for data in result_data:
            product_id = data.get('product_id')
            out_of_stock_qty = data.get('out_of_stock_qty')
            total_value = sum(
                item.get('out_of_stock_qty', 0) for item in result_data)
            if total_value:
                out_of_stock_qty_percentage = \
                    (out_of_stock_qty / total_value) * 100
            else:
                out_of_stock_qty_percentage = 0.0
            data['out_of_stock_qty_percentage'] = round(
                out_of_stock_qty_percentage, 2)
            cost = self.env['product.product'].search([
                ('id', '=', product_id)]).standard_price
            data['cost'] = cost
            data['out_of_stock_value'] = out_of_stock_qty * cost
        if result_data:
            data = {
                'data': result_data,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'inventory_for_next_x_days': self.inventory_for_next_x_days
            }
            return data
        else:
            raise ValidationError("No records found for the given criteria!")

    def action_pdf(self):
        """Function for printing the pdf"""
        data = {
            'model_id': self.id,
            'product_ids': self.product_ids.ids,
            'category_ids': self.category_ids.ids,
            'company_ids': self.company_ids.ids,
            'warehouse_ids': self.warehouse_ids.ids,
            'start_date': self.start_date,
            "end_date": self.end_date,
            "inventory_for_next_x_days": self.inventory_for_next_x_days
        }
        return (
            self.env.ref(
                'inventory_advanced_reports.'
                'report_inventory_out_of_stock_action')
            .report_action(None, data=data))

    def action_excel(self):
        """This function is for printing excel report"""
        data = self.get_report_data()
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'inventory.out.of.stock.report',
                     'options': json.dumps(
                         data, default=fields.date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Excel formats for the Excel report to print"""
        datas = data['data']
        start_date = data['start_date']
        end_date = data['end_date']
        inventory_for_next_x_days = data['inventory_for_next_x_days']
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
        sheet.merge_range('H2:L3', 'Inventory Out OF Stock Report', head)
        bold_format = workbook.add_format(
            {'bold': True, 'font_size': '10px', 'align': 'left'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})
        if start_date and end_date:
            sheet.write('A5', 'Sales History From: ', bold_format)
            sheet.write('B5', start_date, txt)
            sheet.write('A6', 'Sales History Upto: ', bold_format)
            sheet.write('B6', end_date, txt)
            sheet.write('A7', 'Inventory Analysis For Next: ', bold_format)
            sheet.write('B7', str(inventory_for_next_x_days) + ' days', txt)
        headers = ['Product', 'Category', 'Current Stock', 'Incoming',
                   'Outgoing', 'Virtual Stock', 'Sales', 'ADS', 'Demanded QTY',
                   'In Stock Days', 'Out Of Stock Days', 'Out Of Stock Ratio',
                   'Cost Price', 'Out Of Stock QTY', 'Out Of Stock QTY(%)',
                   'Out Of Stock Value(%)', 'Turnover Ratio',
                   'FSN Classification']
        for col, header in enumerate(headers):
            sheet.write(8, col, header, header_style)
        sheet.set_column('A:A', 27, cell_format)
        sheet.set_column('B:B', 24, cell_format)
        sheet.set_column('C:D', 10, cell_format)
        sheet.set_column('E:F', 10, cell_format)
        sheet.set_column('G:H', 10, cell_format)
        sheet.set_column('I:J', 15, cell_format)
        sheet.set_column('K:L', 15, cell_format)
        sheet.set_column('M:N', 15, cell_format)
        sheet.set_column('O:P', 17, cell_format)
        sheet.set_column('Q:R', 15, cell_format)
        sheet.set_column('S:T', 15, cell_format)
        row = 9
        number = 1
        for val in datas:
            sheet.write(row, 0, val['product_code_and_name'], text_style)
            sheet.write(row, 1, val['category_name'], text_style)
            sheet.write(row, 2, val['current_stock'], text_style)
            sheet.write(row, 3, val['incoming_quantity'], text_style)
            sheet.write(row, 4, val['outgoing_quantity'], text_style)
            sheet.write(row, 5, val['virtual_stock'], text_style)
            sheet.write(row, 6, val['sales'], text_style)
            sheet.write(row, 7, val['ads'], text_style)
            sheet.write(row, 8, val['demanded_quantity'], text_style)
            sheet.write(row, 9, val['in_stock_days'], text_style)
            sheet.write(row, 10, val['out_of_stock_days'], text_style)
            sheet.write(row, 11, val['out_of_stock_ratio'], text_style)
            sheet.write(row, 12, val['cost'], text_style)
            sheet.write(row, 13, val['out_of_stock_qty'], text_style)
            sheet.write(row, 14, val['out_of_stock_qty_percentage'], text_style)
            sheet.write(row, 15, val['out_of_stock_value'], text_style)
            sheet.write(row, 16, val['turnover_ratio'], text_style)
            sheet.write(row, 17, val['fsn_classification'], text_style)
            row += 1
            number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def display_report_views(self):
        """Function for displaying the graph and tree view of data"""
        data = self.get_report_data()
        for data_values in data.get('data'):
            data_values['data_id'] = self.id
            self.generate_data(data_values)
        graph_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_out_of_stock_data_report_view_graph').id
        tree_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_out_of_stock_data_report_view_tree').id
        graph_report = self.env.context.get("graph_report", False)
        report_views = [(tree_view_id, 'tree'),
                        (graph_view_id, 'graph')]
        view_mode = "tree,graph"
        if graph_report:
            report_views = [(graph_view_id, 'graph'),
                            (tree_view_id, 'tree')]
            view_mode = "graph,tree"
        return {
            'name': _('Inventory Out Of Stock Report'),
            'domain': [('data_id', '=', self.id)],
            'res_model': 'inventory.out.of.stock.data.report',
            'view_mode': view_mode,
            'type': 'ir.actions.act_window',
            'views': report_views
        }

    def generate_data(self, data_values):
        """Function for creating record in model inventory out of stock data
        report"""
        return self.env['inventory.out.of.stock.data.report'].create({
            'product_id': data_values.get('product_id'),
            'category_id': data_values.get('category_id'),
            'company_id': data_values.get('company_id'),
            'warehouse_id': data_values.get('warehouse_id'),
            'virtual_stock': data_values.get('virtual_stock'),
            'sales': data_values.get('sales'),
            'ads': data_values.get('ads'),
            'demanded_quantity': data_values.get('demanded_quantity'),
            'in_stock_days': data_values.get('in_stock_days'),
            'out_of_stock_days': data_values.get('out_of_stock_days'),
            'out_of_stock_ratio': data_values.get('out_of_stock_ratio'),
            'cost': data_values.get('cost'),
            'out_of_stock_qty': data_values.get('out_of_stock_qty'),
            'out_of_stock_qty_percentage': data_values.get(
                'out_of_stock_qty_percentage'),
            'out_of_stock_value': data_values.get('out_of_stock_value'),
            'turnover_ratio': data_values.get('turnover_ratio'),
            'fsn_classification': data_values.get('fsn_classification'),
            'data_id': self.id,
        })
