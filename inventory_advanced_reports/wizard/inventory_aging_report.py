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


class InventoryAgingReport(models.TransientModel):
    """This model is for creating a wizard for inventory aging report"""
    _name = "inventory.aging.report"
    _description = "Inventory Aging Report"

    product_ids = fields.Many2many(
        "product.product", string="Products",
        help="Select the products you want to generate the report for")
    category_ids = fields.Many2many(
        "product.category", string="Product Categories",
        help="Select the product categories you want to generate the report for"
    )
    company_ids = fields.Many2many(
        'res.company', string="Company",
        help="Select the companies you want to generate the report for"
    )

    def get_report_data(self):
        """Function for returning datas for printing"""
        params = []
        param_count = 0
        query = """
            SELECT 
                CASE
                    WHEN pp.default_code IS NOT NULL 
                        THEN CONCAT(pp.default_code, ' - ', pt.name->>'en_US')
                    ELSE
                        pt.name->>'en_US'
                END AS product_code_and_name, 
                c.complete_name AS category_name,
                c.id AS category_id,
                pp.id AS product_id,
                company.id AS company_id,
                company.name AS company_name,
                 COALESCE(SUM(svl.remaining_qty), 0) AS qty_available,
                (SELECT SUM(sm_inner.product_uom_qty)
                 FROM stock_move sm_inner
                 INNER JOIN res_company company_inner 
                 ON sm_inner.company_id = company_inner.id
                 WHERE sm_inner.product_id = pp.id
                 AND sm_inner.state = 'done'
                 AND sm_inner.date < (
                     SELECT MAX(sm_inner2.date)
                     FROM stock_move sm_inner2
                     WHERE sm_inner2.product_id = pp.id
                     AND sm_inner2.state = 'done'
                     AND company_inner.id = sm_inner2.company_id
                 )
                ) AS prev_qty_available,
                (
            SELECT MIN(sm_inner.date)
            FROM stock_move sm_inner
            WHERE sm_inner.product_id = pp.id
            AND sm_inner.state = 'done'
            AND (company.id IS NULL OR company.id = sm_inner.company_id)
        ) AS receipt_date
            FROM product_product pp
            INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
            INNER JOIN product_category c ON pt.categ_id = c.id
            LEFT JOIN stock_move sm ON sm.product_id = pp.id
            LEFT JOIN stock_picking_type spt ON sm.picking_type_id = spt.id
            LEFT JOIN res_company company ON sm.company_id = company.id
            INNER JOIN stock_valuation_layer svl ON svl.stock_move_id = sm.id
            WHERE pt.detailed_type = 'product'
            AND sm.state = 'done'
                            """
        if self.product_ids or self.category_ids:
            query += " AND ("
        if self.product_ids:
            product_ids = [product_id.id for product_id in self.product_ids]
            query += "pp.id = ANY(%s)"
            params.append(product_ids)
            param_count += 1
        if self.product_ids and self.category_ids:
            query += " OR "
        if self.category_ids:
            category_ids = [category.id for category in self.category_ids]
            params.append(category_ids)
            query += "(pt.categ_id = ANY(%s))"
            param_count += 1
        if self.product_ids or self.category_ids:
            query += ")"
        if self.company_ids:
            company_ids = [company.id for company in self.company_ids]
            query += " AND (sm.company_id = ANY(%s))"
            params.append(company_ids)
            param_count += 1
        query += """
            GROUP BY 
                CASE
                    WHEN pp.default_code IS NOT NULL 
                        THEN CONCAT(pp.default_code, ' - ', pt.name->>'en_US')
                    ELSE
                        pt.name->>'en_US'
                END, 
                c.complete_name,
                company.id, 
                c.id,
                company.name,
                pp.id;
        """
        self.env.cr.execute(query, params)
        result_data = self.env.cr.dictfetchall()
        today = fields.datetime.now().date()
        for row in result_data:
            receipt_date = row.get('receipt_date')
            if receipt_date:
                receipt_date = receipt_date.date()  # Ensure it's a date object
                row['days_since_receipt'] = (today - receipt_date).days
            product = self.env['product.product'].browse(row.get('product_id'))
            standard_price = product.standard_price
            current_stock = row.get('qty_available')
            prev_stock = row.get('prev_qty_available')
            if prev_stock is None:
                prev_stock = current_stock
                row['prev_qty_available'] = current_stock
            if standard_price and current_stock:
                row['current_value'] = current_stock * standard_price
            else:
                row[
                    'current_value'] = 0
            row[
                'prev_value'] = prev_stock * standard_price \
                if prev_stock is not None else 0
            total_current_stock = sum(
                item.get('qty_available') for item in result_data if
                item.get('qty_available') is not None)
            if total_current_stock:
                stock_percentage = (current_stock / total_current_stock) * 100
            else:
                stock_percentage = 0.0
            row['stock_percentage'] = round(stock_percentage, 2)
            current_value = row.get('current_value')
            total_value = sum(
                item.get('current_value', 0) for item in result_data)
            if total_value:
                stock_value_percentage = (current_value / total_value) * 100
            else:
                stock_value_percentage = 0.0
            row['stock_value_percentage'] = round(stock_value_percentage, 2)
        if result_data:
            data = {
                'result_data': result_data,
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

        }
        return (
            self.env.ref(
                'inventory_advanced_reports.report_inventory_aging_action')
            .report_action(None, data=data))

    def action_excel(self):
        """This function is for printing excel report"""
        data = self.get_report_data()
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'inventory.aging.report',
                     'options': json.dumps(
                         data, default=fields.date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Excel sheet format for printing the data"""
        datas = data['result_data']
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
        sheet.merge_range('C2:F3', 'Inventory Aging Report', head)

        headers = ['Product', 'Category', 'Current Stock', 'Current Value',
                   'Stock Quant(%)', 'Stock Value(%)', 'Oldest Stock Age',
                   'Oldest Stock', 'Oldest Stock Value']
        for col, header in enumerate(headers):
            sheet.write(8, col, header, header_style)
        sheet.set_column('A:B', 27, cell_format)
        sheet.set_column('C:D', 13, cell_format)
        sheet.set_column('E:F', 13, cell_format)
        sheet.set_column('G:H', 13, cell_format)
        sheet.set_column('I:J', 15, cell_format)
        row = 9
        number = 1
        for val in datas:
            sheet.write(row, 0, val['product_code_and_name'], text_style)
            sheet.write(row, 1, val['category_name'], text_style)
            sheet.write(row, 2, val['qty_available'], text_style)
            sheet.write(row, 3, val['current_value'], text_style)
            sheet.write(row, 4, val['stock_percentage'], text_style)
            sheet.write(row, 5, val['stock_value_percentage'], text_style)
            sheet.write(row, 6, val['days_since_receipt'], text_style)
            sheet.write(row, 7, val['prev_qty_available'], text_style)
            sheet.write(row, 8, val['prev_value'], text_style)
            row += 1
            number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def display_report_views(self):
        """Function for viewing tree and graph view"""
        data = self.get_report_data()
        for data_values in data.get('result_data'):
            data_values['data_id'] = self.id
            self.generate_data(data_values)
        graph_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_aging_data_report_view_graph').id
        tree_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_aging_data_report_view_tree').id
        graph_report = self.env.context.get("graph_report", False)
        report_views = [(tree_view_id, 'tree'),
                        (graph_view_id, 'graph')]
        view_mode = "tree,graph"
        if graph_report:
            report_views = [(graph_view_id, 'graph'),
                            (tree_view_id, 'tree')]
            view_mode = "graph,tree"
        return {
            'name': _('Inventory Age Report'),
            'domain': [('data_id', '=', self.id)],
            'res_model': 'inventory.aging.data.report',
            'view_mode': view_mode,
            'type': 'ir.actions.act_window',
            'views': report_views
        }

    def generate_data(self, data_values):
        """Function for creating record in inventory aging data report model"""
        return self.env['inventory.aging.data.report'].create({
            'product_id': data_values.get('product_id'),
            'category_id': data_values.get('category_id'),
            'company_id': data_values.get('company_id'),
            'qty_available': data_values.get('qty_available'),
            'current_value': data_values.get('current_value'),
            'stock_percentage': data_values.get('stock_percentage'),
            'stock_value_percentage': data_values.get('stock_value_percentage'),
            'days_since_receipt': data_values.get('days_since_receipt'),
            'prev_qty_available': data_values.get('prev_qty_available'),
            'prev_value': data_values.get('prev_value'),
            'data_id': self.id,
        })
