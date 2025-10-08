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


class InventoryFsnReport(models.TransientModel):
    """This model is for creating a wizard for inventory turnover report."""
    _name = 'inventory.fsn.report'
    _description = 'Inventory FSN Report'

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

    def get_report_data(self):
        """Function for returning data for printing"""
        fsn = dict(self._fields['fsn'].selection).get(self.fsn)
        if self.start_date > self.end_date:
            raise ValidationError("Start date can't be greater than end date")
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
                CASE
                    WHEN sales > 0 
                    THEN ROUND((sales / NULLIF(average_stock, 0)), 2)
                    ELSE 0
                END AS turnover_ratio,
                CASE
                    WHEN
                        CASE
                            WHEN sales > 0 
                            THEN ROUND((sales / NULLIF(average_stock, 0)), 2)
                            ELSE 0
                        END > 3 THEN 'Fast Moving'
                    WHEN
                        CASE
                            WHEN sales > 0 
                            THEN ROUND((sales / NULLIF(average_stock, 0)), 2)
                            ELSE 0
                        END >= 1 AND
                        CASE
                            WHEN sales > 0 
                            THEN ROUND((sales / NULLIF(average_stock, 0)), 2)
                            ELSE 0
                        END <= 3 THEN 'Slow Moving'
                    ELSE 'Non Moving'
                END AS fsn_classification
            FROM
                (SELECT
                    pp.id AS product_id,
                    pt.categ_id AS category_id,
                    CASE
                        WHEN pp.default_code IS NOT NULL 
                            THEN CONCAT(pp.default_code, ' - ', pt.name->>'en_US')
                        ELSE
                            pt.name->>'en_US'
                    END AS product_code_and_name, 
                    pc.complete_name AS category_name,
                    company.id AS company_id,
                    COALESCE(sw_dest.id, sw_src.id) AS warehouse_id,
                    (SUM(CASE WHEN sm.date <= %s AND sl_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sl_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END)) AS opening_stock,
                    (SUM(CASE WHEN sm.date <= %s AND sl_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sl_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END)) AS closing_stock,
                    SUM(CASE WHEN sm.date BETWEEN %s AND %s 
                    AND sl_dest.usage = 'customer' 
                    THEN sm.product_uom_qty ELSE 0 END) AS sales,
                    ((SUM(CASE WHEN sm.date <= %s 
                    AND sl_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sl_src.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END))+
                    (SUM(CASE WHEN sm.date <= %s AND sl_dest.usage = 'internal' 
                    THEN sm.product_uom_qty ELSE 0 END) -
                    SUM(CASE WHEN sm.date <= %s AND sl_src.usage = 'internal' 
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
                    stock_location sl_dest ON sm.location_dest_id = sl_dest.id
                JOIN
                    stock_location sl_src ON sm.location_id = sl_src.id
                LEFT JOIN
                    stock_warehouse sw_dest ON sl_dest.warehouse_id = sw_dest.id
                LEFT JOIN
                    stock_warehouse sw_src ON sl_src.warehouse_id = sw_src.id
                WHERE
                    sm.state = 'done'
        """
        params = [
            start_date, start_date, end_date, end_date, start_date, end_date,
            start_date, start_date, end_date, end_date
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
            category_ids = [category_id.id for category_id in self.category_ids]
            query += "pt.categ_id IN %s"
            params.append(tuple(category_ids))
        if self.product_ids or self.category_ids:
            query += ")"
        if self.company_ids:
            query += " AND company.id IN %s"
            params.append(tuple(self.company_ids.ids))
        if self.warehouse_ids:
            query += " AND (COALESCE(sw_dest.id, sw_src.id) IN %s)"
            params.append(tuple(self.warehouse_ids.ids))
        query += """
                GROUP BY pp.id, pt.categ_id,
                CASE
                    WHEN pp.default_code IS NOT NULL 
                        THEN CONCAT(pp.default_code, ' - ', pt.name->>'en_US')
                    ELSE
                        pt.name->>'en_US'
                END, pc.complete_name, company.id, COALESCE(sw_dest.id, sw_src.id)
                ) AS subquery
        """
        self.env.cr.execute(query, tuple(params))
        result_data = self.env.cr.dictfetchall()
        for fsn_data in result_data:
            if fsn_data.get('fsn_classification') == str(fsn):
                filtered_product_stock.append(fsn_data)
        if fsn == 'All' and not result_data:
            raise ValidationError("No corresponding data to print")
        elif fsn != 'All' and filtered_product_stock == []:
            raise ValidationError("No corresponding data to print")
        data = {
            'data': result_data if fsn == 'All' else filtered_product_stock,
            'start_date': start_date,
            'end_date': end_date
        }
        return data

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
            "fsn": dict(self._fields['fsn'].selection).get(self.fsn)
        }
        return (
            self.env.ref(
                'inventory_advanced_reports.report_inventory_fsn_action')
            .report_action(None, data=data))

    def action_excel(self):
        """This function is for printing excel report"""
        data = self.get_report_data()
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'inventory.fsn.report',
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
        sheet.merge_range('B2:F3', 'Inventory FSN Report', head)
        bold_format = workbook.add_format(
            {'bold': True, 'font_size': '10px', 'align': 'left'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})
        if start_date and end_date:
            sheet.write('A5', 'Start Date: ', bold_format)
            sheet.write('B5', start_date, txt)
            sheet.write('A6', 'End Date: ', bold_format)
            sheet.write('B6', end_date, txt)
        headers = ['Product', 'Category', 'Opening Stock', 'Closing Value',
                   'Average Stock', 'Sales', 'Turnover Ratio',
                   'FSN Classification']
        for col, header in enumerate(headers):
            sheet.write(8, col, header, header_style)
        sheet.set_column('A:A', 27, cell_format)
        sheet.set_column('B:B', 24, cell_format)
        sheet.set_column('C:D', 13, cell_format)
        sheet.set_column('E:F', 13, cell_format)
        sheet.set_column('G:H', 13, cell_format)
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
            sheet.write(row, 7, val['fsn_classification'], text_style)
            row += 1
            number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def display_report_views(self):
        """Function for displaying graph and tree view of data"""
        data = self.get_report_data()
        for data_values in data.get('data'):
            data_values['data_id'] = self.id
            self.generate_data(data_values)
        graph_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_fsn_data_report_view_graph').id
        tree_view_id = self.env.ref(
            'inventory_advanced_reports.'
            'inventory_fsn_data_report_view_tree').id
        graph_report = self.env.context.get("graph_report", False)
        report_views = [(tree_view_id, 'tree'),
                        (graph_view_id, 'graph')]
        view_mode = "tree,graph"
        if graph_report:
            report_views = [(graph_view_id, 'graph'),
                            (tree_view_id, 'tree')]
            view_mode = "graph,tree"
        return {
            'name': _('Inventory FSN Report'),
            'domain': [('data_id', '=', self.id)],
            'res_model': 'inventory.fsn.data.report',
            'view_mode': view_mode,
            'type': 'ir.actions.act_window',
            'views': report_views
        }

    def generate_data(self, data_values):
        """Function for creating data in model inventory fsn data report
        model"""
        return self.env['inventory.fsn.data.report'].create({
            'product_id': data_values.get('product_id'),
            'category_id': data_values.get('category_id'),
            'company_id': data_values.get('company_id'),
            'warehouse_id': data_values.get('warehouse_id'),
            'opening_stock': data_values.get('opening_stock'),
            'closing_stock': data_values.get('closing_stock'),
            'average_stock': data_values.get('average_stock'),
            'sales': data_values.get('sales'),
            'turnover_ratio': data_values.get('turnover_ratio'),
            'fsn_classification': data_values.get('fsn_classification'),
            'data_id': self.id,
        })
