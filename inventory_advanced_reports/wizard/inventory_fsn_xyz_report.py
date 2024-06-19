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


class InventoryFsnXyzReport(models.TransientModel):
    """This model is for creating a wizard for inventory turnover report."""
    _name = 'inventory.fsn.xyz.report'
    _description = 'Inventory FSN-XYZ Report'

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
    fsn = fields.Selection([
        ('fast_moving', 'Fast Moving'),
        ('slow_moving', 'Slow Moving'),
        ('non_moving', 'Non Moving'),
        ('all', 'All')
    ], string='FSN Category', default="all", required=True)
    xyz = fields.Selection([('x', 'X'), ('y', 'Y'), ('z', 'Z'), ('all', 'All')],
                           string="XYZ Classification", default='all',
                           required=True)

    def get_report_data(self):
        """Function for returning datas for printing"""
        fsn = dict(self._fields['fsn'].selection).get(self.fsn)
        xyz = dict(self._fields['xyz'].selection).get(self.xyz)
        start_date = self.start_date
        end_date = self.end_date
        filtered_product_stock = []
        query = """
                SELECT
                product_id,
                product_code_and_name,
                category_id,
                category_name,
                company_id,
                warehouse_id,
                opening_stock,
                closing_stock,
                sales,
                average_stock,
                current_stock,
                stock_value,
                        CASE
                            WHEN sales > 0 THEN 
                            ROUND((sales / NULLIF(average_stock, 0)), 2)
                            ELSE 0
                        END AS turnover_ratio,
                        CASE
                            WHEN
                                CASE
                                    WHEN sales > 0 THEN 
                                    ROUND((sales / NULLIF(average_stock, 0)), 2)
                                    ELSE 0
                                END > 3 THEN 'Fast Moving'
                            WHEN
                                CASE
                                    WHEN sales > 0 THEN 
                                    ROUND((sales / NULLIF(average_stock, 0)), 2)
                                    ELSE 0
                                END >= 1 AND
                                CASE
                                    WHEN sales > 0 THEN 
                                    ROUND((sales / NULLIF(average_stock, 0)), 2)
                                    ELSE 0
                                END <= 3 THEN 'Slow Moving'
                            ELSE 'Non Moving'
                            END AS fsn_classification,
                            stock_percentage,
                            SUM(stock_percentage) 
                            OVER (ORDER BY stock_value DESC) 
                            AS cumulative_stock_percentage,
                            CASE
                WHEN SUM(stock_percentage) OVER (ORDER BY stock_value DESC) < 70 
                THEN 'X'
                WHEN SUM(stock_percentage) 
                OVER (ORDER BY stock_value DESC) >= 70 AND 
                SUM(stock_percentage) OVER (ORDER BY stock_value DESC) <= 90 
                THEN 'Y'
                ELSE 'Z'
            END AS xyz_classification,
            CONCAT(
                CASE
                    WHEN
                        CASE
                            WHEN sales > 0 THEN 
                            ROUND((sales / NULLIF(average_stock, 0)), 2)
                            ELSE 0
                        END > 3 THEN 'F'
                    WHEN
                        CASE
                            WHEN sales > 0 THEN 
                            ROUND((sales / NULLIF(average_stock, 0)), 2)
                            ELSE 0
                        END >= 1 AND
                        CASE
                            WHEN sales > 0 THEN 
                            ROUND((sales / NULLIF(average_stock, 0)), 2)
                            ELSE 0
                        END <= 3 THEN 'S'
                    ELSE 'N'
                END,
                CASE
                    WHEN SUM(stock_percentage) 
                    OVER (ORDER BY stock_value DESC) < 70 THEN 'X'
                    WHEN SUM(stock_percentage) 
                    OVER (ORDER BY stock_value DESC) >= 70 
                    AND SUM(stock_percentage) 
                    OVER (ORDER BY stock_value DESC) <= 90 THEN 'Y'
                    ELSE 'Z'
                END
            ) AS combined_classification
            FROM
                (SELECT
                    pp.id AS product_id,
                    pt.categ_id AS category_id,
                    CASE
                        WHEN pp.default_code IS NOT NULL 
                            THEN CONCAT(pp.default_code, ' - ', 
                            pt.name->>'en_US')
                        ELSE
                            pt.name->>'en_US'
                    END AS product_code_and_name, 
                    pc.complete_name AS category_name,
                    company.id AS company_id,
                    sw.id AS warehouse_id,
                    SUM(svl.remaining_qty) AS current_stock,
                    SUM(svl.remaining_value) AS stock_value,
                    COALESCE(ROUND((SUM(svl.remaining_value) / 
                    NULLIF(SUM(SUM(svl.remaining_value)) 
                    OVER (), 0)) * 100, 2),0) AS stock_percentage,
                    (SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END)) AS opening_stock,
                    (SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END)) AS closing_stock,
                    SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                    AND sld_dest.usage = 'customer' 
                    THEN sm.product_uom_qty ELSE 0 END) AS sales,
                    ((SUM(CASE WHEN sm.date <= %s 
                    AND sld_dest.usage = 'internal' THEN sm.product_uom_qty 
                    ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END))+
                    (SUM(CASE WHEN sm.date <= %s AND sld_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sld_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END)))/2 AS average_stock
                FROM
                stock_move sm
            JOIN
                product_product pp ON sm.product_id = pp.id
            JOIN
                product_template pt ON pp.product_tmpl_id = pt.id
            JOIN
                product_category pc ON pt.categ_id = pc.id
            JOIN
                res_company company ON company.id = sm.company_id
            JOIN
                stock_warehouse sw ON sw.company_id = company.id
            JOIN
                stock_valuation_layer svl ON svl.stock_move_id = sm.id    
            LEFT JOIN
                stock_location sld_dest ON sm.location_dest_id = sld_dest.id
            LEFT JOIN
                stock_location sld_src ON sm.location_id = sld_src.id
            WHERE
                sm.state = 'done'
                AND pp.active = TRUE
                AND pt.active = TRUE
                AND pt.type = 'product'
                AND svl.remaining_value IS NOT NULL
                """
        params = [
            start_date, start_date, end_date, end_date, start_date, end_date,
            start_date, start_date, end_date, end_date
        ]
        sub_queries = []
        sub_params = []
        param_count = 0
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
            category_ids = [category_id.id for category_id in self.category_ids]
            query += "pt.categ_id IN %s"
            params.append(tuple(category_ids))
            param_count += 1
        if self.product_ids or self.category_ids:
            query += ")"
        if self.company_ids:
            query += f" AND sm.company_id IN %s"  # Specify the table alias
            sub_params.append(tuple(self.company_ids.ids))
            param_count += 1
        if self.warehouse_ids:
            query += f" AND sw.id IN %s"  # Specify the table alias
            sub_params.append(tuple(self.warehouse_ids.ids))
            param_count += 1
        if sub_queries:
            query += " AND " + " AND ".join(sub_queries)
        query += """
                GROUP BY
                pp.id,pt.name, pt.categ_id,pc.complete_name, company.id, sw.id  
                ) AS subquery
                ORDER BY stock_value DESC
                """
        self.env.cr.execute(query, tuple(params + sub_params))
        result_data = self.env.cr.dictfetchall()
        for fsn_data in result_data:
            if (
                    (fsn == 'All' and xyz == 'All') or
                    (fsn == 'All' and fsn_data.get('xyz_classification') == str(
                        xyz)) or
                    (xyz == 'All' and fsn_data.get('fsn_classification') == str(
                        fsn)) or
                    (fsn_data.get('fsn_classification') == str(
                        fsn) and fsn_data.get('xyz_classification') == str(xyz))
            ):
                filtered_product_stock.append(fsn_data)
        if (fsn == 'All' or xyz == 'All') and not result_data:
            raise ValidationError("No corresponding data to print")
        elif not filtered_product_stock:
            raise ValidationError("No corresponding data to print")
        data = {
            'data': filtered_product_stock,
            'start_date': start_date,
            'end_date': end_date
        }
        return data

    def action_pdf(self):
        """Function for printing pdf report"""
        data = {
            'model_id': self.id,
            'product_ids': self.product_ids.ids,
            'category_ids': self.category_ids.ids,
            'company_ids': self.company_ids.ids,
            'warehouse_ids': self.warehouse_ids.ids,
            'start_date': self.start_date,
            "end_date": self.end_date,
            "fsn": dict(self._fields['fsn'].selection).get(self.fsn),
            "xyz": dict(self._fields['xyz'].selection).get(self.xyz)
        }
        return (
            self.env.ref(
                'inventory_advanced_reports.report_inventory_fsn_xyz_action')
            .report_action(None, data=data))

    def action_excel(self):
        """This function is for printing excel report"""
        data = self.get_report_data()
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'inventory.fsn.xyz.report',
                     'options': json.dumps(
                         data, default=fields.date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Excel sheet format for printing the data"""
        datas = data['data']
        start_date = data['start_date']
        end_date = data['end_date']
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
        sheet.merge_range('E2:I3', 'Inventory FSN-XYZ Report', head)
        bold_format = workbook.add_format(
            {'bold': True, 'font_size': '10px', 'align': 'left'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})
        if start_date and end_date:
            sheet.write('A5', 'Start Date: ', bold_format)
            sheet.write('B5', start_date, txt)
            sheet.write('A6', 'End Date: ', bold_format)
            sheet.write('B6', end_date, txt)
        headers = ['Product', 'Category', 'Opening Stock', 'Closing Stock',
                   'Average Stock', 'Sales', 'Turnover Ratio', 'Current Stock',
                   'Stock Value', 'Stock Value(%)', 'Cumulative Value(%)',
                   'FSN Classification', 'XYZ Classification',
                   'FSN-XYZ Classification']
        for col, header in enumerate(headers):
            sheet.write(8, col, header, header_style)
        sheet.set_column('A:A', 27, cell_format)
        sheet.set_column('B:B', 24, cell_format)
        sheet.set_column('C:D', 13, cell_format)
        sheet.set_column('E:F', 13, cell_format)
        sheet.set_column('G:H', 15, cell_format)
        sheet.set_column('I:J', 15, cell_format)
        sheet.set_column('K:L', 17, cell_format)
        sheet.set_column('M:N', 17, cell_format)
        row = 9
        number = 1
        for val in datas:
            sheet.write(row, 0, val['product_code_and_name'], text_style)
            sheet.write(row, 1, val['category_name'], text_style)
            sheet.write(row, 2, val['opening_stock'], text_style)
            sheet.write(row, 3, val['closing_stock'], text_style)
            sheet.write(row, 4, val['average_stock'], text_style)
            sheet.write(row, 5, val['sales'], text_style)
            sheet.write(row, 6, val['turnover_ratio'], text_style)
            sheet.write(row, 7, val['current_stock'], text_style)
            sheet.write(row, 8, val['stock_value'], text_style)
            sheet.write(row, 9, val['stock_percentage'], text_style)
            sheet.write(row, 10, val['cumulative_stock_percentage'], text_style)
            sheet.write(row, 11, val['fsn_classification'], text_style)
            sheet.write(row, 12, val['xyz_classification'], text_style)
            sheet.write(row, 13, val['combined_classification'], text_style)
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
            'inventory_fsn_xyz_data_report_view_graph').id
        tree_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_fsn_xyz_data_report_view_tree').id
        graph_report = self.env.context.get("graph_report", False)
        report_views = [(tree_view_id, 'tree'),
                        (graph_view_id, 'graph')]
        view_mode = "tree,graph"
        if graph_report:
            report_views = [(graph_view_id, 'graph'),
                            (tree_view_id, 'tree')]
            view_mode = "graph,tree"
        return {
            'name': _('Inventory FSN-XYZ Report'),
            'domain': [('data_id', '=', self.id)],
            'res_model': 'inventory.fsn.xyz.data.report',
            'view_mode': view_mode,
            'type': 'ir.actions.act_window',
            'views': report_views
        }

    def generate_data(self, data_values):
        """Function for creating a record in model inventory fsn xyz data
        'report"""
        return self.env['inventory.fsn.xyz.data.report'].create({
            'product_id': data_values.get('product_id'),
            'category_id': data_values.get('category_id'),
            'company_id': data_values.get('company_id'),
            'average_stock': data_values.get('average_stock'),
            'sales': data_values.get('sales'),
            'turnover_ratio': data_values.get('turnover_ratio'),
            'current_stock': data_values.get('current_stock'),
            'stock_value': data_values.get('stock_value'),
            'fsn_classification': data_values.get('fsn_classification'),
            'xyz_classification': data_values.get('xyz_classification'),
            'combined_classification': data_values.get(
                'combined_classification'),
            'data_id': self.id,
        })
