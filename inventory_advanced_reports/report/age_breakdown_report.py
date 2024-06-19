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


class AgeBreakdownReport(models.AbstractModel):
    """Create an abstract model for passing reporting values"""
    _name = 'report.inventory_advanced_reports.report_inventory_breakdown'
    _description = 'Age Breakdown Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """This function has working in get the pdf report."""
        values = data
        product_ids = data['product_ids']
        category_ids = data['category_ids']
        company_ids = data['company_ids']
        age_breakdown_days = data['age_breakdown_days']
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
        params.extend([age_breakdown_days] * 16)
        if product_ids or category_ids:
            query += " AND ("
        if product_ids:
            product_ids = [product_id for product_id in product_ids]
            query += "pp.id = ANY(%s)"
            params.append(product_ids)
            param_count += 1
        if product_ids and category_ids:
            query += " OR "
        if category_ids:
            category_ids = [category for category in category_ids]
            params.append(category_ids)
            query += "(pt.categ_id = ANY(%s))"
            param_count += 1
        if product_ids or category_ids:
            query += ")"
        if company_ids:
            company_ids = [company for company in company_ids]
            query += " AND (sm.company_id = ANY(%s))"  # Specify the table alias
            params.append(company_ids)
            param_count += 1
        query += """
                    GROUP BY
                                CASE
                                    WHEN pp.default_code IS NOT NULL 
                                        THEN CONCAT(pp.default_code, ' - ', 
                                        pt.name->>'en_US')
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
        main_header = age_breakdown_days
        if result_data:
            return {
                'doc_ids': docids,
                'doc_model': 'report.inventory_advanced_reports.'
                             'report_inventory_breakdown',
                'data': values,
                'options': result_data,
                'main_header': self.get_header(main_header)
            }
        else:
            raise ValidationError("No records found for the given criteria!")

    def get_header(self, main_header):
        """For getting the header for the report"""
        age_breakdown1 = main_header
        age_breakdown2 = main_header * 2
        age_breakdown3 = main_header * 3
        age_breakdown4 = main_header * 4
        return ['1-' + str(age_breakdown1),
                str(age_breakdown1 + 1) + '-' + str(age_breakdown2),
                str(age_breakdown2 + 1) + '-' + str(age_breakdown3),
                str(age_breakdown3 + 1) + '-' + str(age_breakdown4),
                'ABOVE ' + str(age_breakdown4)]
