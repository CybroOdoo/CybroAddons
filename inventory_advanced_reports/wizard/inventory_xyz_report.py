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


class InventoryXyzReport(models.TransientModel):
    """This model is for creating a wizard for inventory aging report"""
    _name = "inventory.xyz.report"
    _description = "Inventory XYZ Report"

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
    xyz = fields.Selection([('x', 'X'), ('y', 'Y'), ('z', 'Z'), ('all', 'All')],
                           string="XYZ Classification", default='all',
                           required=True)

    def get_report_data(self):
        """Function for returning data to print"""
        xyz = dict(self._fields['xyz'].selection).get(self.xyz)
        params = []
        param_count = 0
        query = """
                SELECT 
                    CASE
                        WHEN pp.default_code IS NOT NULL 
                            THEN CONCAT(pp.default_code, ' - ', 
                            pt.name->>'en_US')
                        ELSE
                            pt.name->>'en_US'
                    END AS product_code_and_name,
                    svl.company_id,
                    company.name AS company_name,
                    svl.product_id,
                    pt.categ_id AS category_id,
                    c.complete_name AS category_name,
                    SUM(svl.remaining_qty) AS current_stock,
                    SUM(svl.remaining_value) AS stock_value
                FROM stock_valuation_layer svl
                INNER JOIN res_company company ON company.id = svl.company_id
                INNER JOIN product_product pp ON pp.id = svl.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                INNER JOIN product_category c ON c.id = pt.categ_id
                WHERE pp.active = TRUE
                    AND pt.active = TRUE
                    AND pt.type = 'product'
                    AND svl.remaining_value IS NOT NULL
                """
        if self.company_ids:
            company_ids = [company_id.id for company_id in self.company_ids]
            query += f" AND (company.id IS NULL OR company.id = ANY(%s))"
            params.append(company_ids)
            param_count += 1
        if self.product_ids or self.category_ids:
            query += " AND ("
            if self.product_ids:
                product_ids = [product_id.id for product_id in self.product_ids]
                query += f"pp.id = ANY(%s)"
                params.append(product_ids)
                param_count += 1
            if self.product_ids and self.category_ids:
                query += " OR "
            if self.category_ids:
                category_ids = [category_id.id for category_id in
                                self.category_ids]
                query += f"c.id = ANY(%s)"
                params.append(category_ids)
                param_count += 1
            query += ")"
        query += """
                GROUP BY 
                svl.company_id,
                company.name,
                svl.product_id,
                CASE
                    WHEN pp.default_code IS NOT NULL 
                        THEN CONCAT(pp.default_code, ' - ', pt.name->>'en_US')
                    ELSE
                        pt.name->>'en_US'
                END,
                pt.categ_id,
                c.complete_name
                ORDER BY SUM(svl.remaining_value) DESC;
                        """
        self.env.cr.execute(query, params)
        result_data = self.env.cr.dictfetchall()
        total_current_value = 0
        cumulative_stock = 0
        filtered_stock = []
        for row in result_data:
            current_value = row.get('stock_value')
            total_current_value += current_value
        for value in result_data:
            current_value = value.get('stock_value')
            if total_current_value != 0 and current_value:
                stock_percentage = (current_value / total_current_value) * 100
            else:
                stock_percentage = 0.0
            value['stock_percentage'] = round(stock_percentage, 2)
            cumulative_stock += value['stock_percentage']
            value['cumulative_stock_percentage'] = round(cumulative_stock, 2)
            if cumulative_stock < 70:
                xyz_classification = 'X'
            elif 70 <= cumulative_stock <= 90:
                xyz_classification = 'Y'
            else:
                xyz_classification = 'Z'
            value['xyz_classification'] = xyz_classification
        if result_data:
            for xyz_class in result_data:
                if xyz_class.get('xyz_classification') == str(xyz):
                    filtered_stock.append(xyz_class)
            if xyz == 'All' and not result_data:
                raise ValidationError("No corresponding data to print")
            elif xyz != 'All' and filtered_stock == []:
                raise ValidationError("No corresponding data to print")
            data = {
                'data': result_data if xyz == 'All' else filtered_stock,
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
            "xyz": dict(self._fields['xyz'].selection).get(self.xyz)

        }
        return (
            self.env.ref(
                'inventory_advanced_reports.report_inventory_xyz_action')
            .report_action(None, data=data))

    def action_excel(self):
        """This function is for printing excel report"""
        data = self.get_report_data()
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'inventory.xyz.report',
                     'options': json.dumps
                     (data, default=fields.date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Excel formats for printing data in Excel sheets"""
        datas = data['data']
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
        sheet.merge_range('B2:E3', 'Inventory XYZ Report', head)
        headers = ['Product', 'Category', 'Current Stock', 'Stock Value',
                   'Cumulative Stock', 'XYZ Calculation']
        for col, header in enumerate(headers):
            sheet.write(8, col, header, header_style)
        sheet.set_column('A:B', 27, cell_format)
        sheet.set_column('C:D', 15, cell_format)
        sheet.set_column('E:F', 15, cell_format)
        row = 9
        number = 1
        for val in datas:
            sheet.write(row, 0, val['product_code_and_name'], text_style)
            sheet.write(row, 1, val['category_name'], text_style)
            sheet.write(row, 2, val['current_stock'], text_style)
            sheet.write(row, 3, val['stock_value'], text_style)
            sheet.write(row, 4, val['stock_percentage'], text_style)
            sheet.write(row, 5, val['cumulative_stock_percentage'], text_style)
            sheet.write(row, 5, val['xyz_classification'], text_style)
            row += 1
            number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def display_report_views(self):
        """Function for displaying graph and tree view of the data"""
        data = self.get_report_data()
        for data_values in data.get('data'):
            data_values['data_id'] = self.id
            self.generate_data(data_values)
        graph_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_xyz_data_report_view_graph').id
        tree_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_xyz_data_report_view_tree').id
        graph_report = self.env.context.get("graph_report", False)
        report_views = [(tree_view_id, 'tree'),
                        (graph_view_id, 'graph')]
        view_mode = "tree,graph"
        if graph_report:
            report_views = [(graph_view_id, 'graph'),
                            (tree_view_id, 'tree')]
            view_mode = "graph,tree"
        return {
            'name': _('Inventory XYZ Report'),
            'domain': [('data_id', '=', self.id)],
            'res_model': 'inventory.xyz.data.report',
            'view_mode': view_mode,
            'type': 'ir.actions.act_window',
            'views': report_views
        }

    def generate_data(self, data_values):
        """Function for creating record in the model inventory cyz data
        report"""
        return self.env['inventory.xyz.data.report'].create({
            'product_id': data_values.get('product_id'),
            'category_id': data_values.get('category_id'),
            'company_id': data_values.get('company_id'),
            'current_stock': data_values.get('current_stock'),
            'stock_value': data_values.get('stock_value'),
            'stock_percentage': data_values.get('stock_percentage'),
            'cumulative_stock_percentage': data_values.get(
                'cumulative_stock_percentage'),
            'xyz_classification': data_values.get('xyz_classification'),
            'data_id': self.id,
        })
