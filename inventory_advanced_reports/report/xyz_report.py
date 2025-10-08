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
from odoo import api, models
from odoo.exceptions import ValidationError


class XyzReport(models.AbstractModel):
    """Create an abstract model for passing reporting values"""
    _name = 'report.inventory_advanced_reports.report_inventory_xyz'
    _description = 'XYZ Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """This function has working in get the pdf report."""
        values = data
        product_ids = data['product_ids']
        category_ids = data['category_ids']
        company_ids = data['company_ids']
        xyz = data['xyz']
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
            svl.company_id,
            company.name AS company_name,
            svl.product_id,
            pt.categ_id AS product_category_id,
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
        if company_ids:
            company_ids = [company_id for company_id in company_ids]
            query += f" AND (company.id IS NULL OR company.id = ANY(%s))"
            params.append(company_ids)
            param_count += 1
        if product_ids or category_ids:
            query += " AND ("
            if product_ids:
                product_ids = [product_id for product_id in product_ids]
                query += f"pp.id = ANY(%s)"
                params.append(product_ids)
                param_count += 1
            if product_ids and category_ids:
                query += " OR "
            if category_ids:
                category_ids = [category_id for category_id in
                                category_ids]
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
            return {
                'doc_ids': docids,
                'doc_model':
                    'report.inventory_advanced_reports.report_inventory_xyz',
                'data': values,
                'options': result_data if xyz == 'All' else filtered_stock,
            }
        else:
            raise ValidationError("No records found for the given criteria!")
