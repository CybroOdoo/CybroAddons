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


class InventoryAgeBreakdownReport(models.TransientModel):
    """This model is for creating a wizard for inventory age breakdown report"""
    _name = "inventory.age.breakdown.report"
    _description = "Inventory Age Breakdown Report"

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
    age_breakdown_days = fields.Integer(string="Age Breakdown Days", default=30)

    def get_report_data(self):
        """Function to return necessary data for printing"""
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
            SUM(svl.remaining_value) AS stock_value,
            SUM(CASE
                WHEN age.days_between >= 1 AND age.days_between <= %s 
                THEN svl.remaining_qty
                ELSE 0
            END) AS "age_breakdown_qty_1",
            SUM(CASE
                WHEN age.days_between >= %s+1 AND age.days_between <= %s*2 
                THEN svl.remaining_qty
                ELSE 0
            END) AS "age_breakdown_qty_2",
            SUM(CASE
                WHEN age.days_between >=  (%s*2)+1 AND age.days_between <= %s*3 
                THEN svl.remaining_qty
                ELSE 0
            END) AS "age_breakdown_qty_3",
            SUM(CASE
                WHEN age.days_between >= (%s*3)+1 AND age.days_between <= %s*4 
                THEN svl.remaining_qty
                ELSE 0
            END) AS "age_breakdown_qty_4",
            SUM(CASE
                WHEN age.days_between >= (%s*4)+1 THEN svl.remaining_qty
                ELSE 0
            END) AS "age_breakdown_qty_5",
            SUM(CASE
                WHEN age.days_between >= 1 AND age.days_between <= %s 
                THEN svl.remaining_value
                ELSE 0
            END) AS "age_breakdown_value_1",
            SUM(CASE
                WHEN age.days_between >= %s+1 AND age.days_between <= %s*2 
                THEN svl.remaining_value
                ELSE 0
            END) AS "age_breakdown_value_2",
            SUM(CASE
                WHEN age.days_between >= (%s*2)+1 AND age.days_between <= %s*3 
                THEN svl.remaining_value
                ELSE 0
            END) AS "age_breakdown_value_3",
            SUM(CASE
                WHEN age.days_between >= (%s*3)+1 AND age.days_between <= %s*4 
                THEN svl.remaining_value
                ELSE 0
            END) AS "age_breakdown_value_4",
            SUM(CASE
                WHEN age.days_between >= (%s*4)+1 THEN svl.remaining_value
                ELSE 0
            END) AS "age_breakdown_value_5"
            FROM product_product pp
            INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
            INNER JOIN product_category c ON pt.categ_id = c.id
            LEFT JOIN stock_move sm ON sm.product_id = pp.id
            LEFT JOIN stock_picking_type spt ON sm.picking_type_id = spt.id
            LEFT JOIN res_company company ON sm.company_id = company.id
            LEFT JOIN LATERAL (
                SELECT EXTRACT(day FROM CURRENT_DATE - sm.date) AS days_between
            ) AS age ON true
            INNER JOIN stock_valuation_layer svl ON svl.stock_move_id = sm.id
            WHERE pt.detailed_type = 'product'
                AND sm.state = 'done'
                AND svl.remaining_value IS NOT NULL
                """
        params.extend([self.age_breakdown_days] * 16)
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
        main_header = self.age_breakdown_days
        if result_data:
            data = {
                'result_data': result_data,
                'main_header': main_header
            }
            return data
        else:
            raise ValidationError("No records found for the given criteria!")

    def get_header(self, main_header):
        """This function for getting the header in report"""
        age_breakdown1 = main_header
        age_breakdown2 = main_header * 2
        age_breakdown3 = main_header * 3
        age_breakdown4 = main_header * 4
        return ['1-' + str(age_breakdown1),
                str(age_breakdown1 + 1) + '-' + str(age_breakdown2),
                str(age_breakdown2 + 1) + '-' + str(age_breakdown3),
                str(age_breakdown3 + 1) + '-' + str(age_breakdown4),
                'ABOVE ' + str(age_breakdown4)]

    def action_pdf(self):
        """This function is for printing pdf report"""
        data = {
            'model_id': self.id,
            'product_ids': self.product_ids.ids,
            'category_ids': self.category_ids.ids,
            'company_ids': self.company_ids.ids,
            'age_breakdown_days': self.age_breakdown_days,
        }
        return (
            self.env.ref(
                'inventory_advanced_reports.'
                'report_inventory_age_breakdown_action')
            .report_action(None, data=data))

    def action_excel(self):
        """This function is for printing excel report"""
        data = self.get_report_data()
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'inventory.age.breakdown.report',
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
        main_header = data['main_header']
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
        sheet.merge_range('C2:I3', 'Inventory Age Breakdown Report', head)

        headers = ['Product', 'Category', 'Total Stock', 'Stock Value', 'Stock',
                   'Value', 'Stock', 'Value', 'Stock', 'Value', 'Stock',
                   'Value', 'Stock', 'Value']
        main_headers = self.get_header(main_header)
        for col, header in enumerate(main_headers):
            sheet.merge_range(7, col * 2 + 4, 7, col * 2 + 5, header,
                              header_style)
        for col, header in enumerate(headers):
            sheet.write(8, col, header, header_style)
        sheet.set_column('A:B', 27, cell_format)
        sheet.set_column('C:D', 13, cell_format)
        row = 9
        number = 1
        for val in datas:
            sheet.write(row, 0, val['product_code_and_name'], text_style)
            sheet.write(row, 1, val['category_name'], text_style)
            sheet.write(row, 2, val['qty_available'], text_style)
            sheet.write(row, 3, val['stock_value'], text_style)
            sheet.write(row, 4, val['age_breakdown_qty_1'], text_style)
            sheet.write(row, 5, val['age_breakdown_value_1'], text_style)
            sheet.write(row, 6, val['age_breakdown_qty_2'], text_style)
            sheet.write(row, 7, val['age_breakdown_value_2'], text_style)
            sheet.write(row, 8, val['age_breakdown_qty_3'], text_style)
            sheet.write(row, 9, val['age_breakdown_value_3'], text_style)
            sheet.write(row, 10, val['age_breakdown_qty_4'], text_style)
            sheet.write(row, 11, val['age_breakdown_value_4'], text_style)
            sheet.write(row, 12, val['age_breakdown_qty_5'], text_style)
            sheet.write(row, 13, val['age_breakdown_value_5'], text_style)
            row += 1
            number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
