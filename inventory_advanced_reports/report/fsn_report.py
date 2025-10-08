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
from datetime import datetime

from odoo.exceptions import ValidationError


class FsnReport(models.AbstractModel):
    """Create an abstract model for passing reporting values"""
    _name = 'report.inventory_advanced_reports.report_inventory_fsn'
    _description = 'FSN Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """This function has working in get the pdf report."""
        values = data
        if data is None or not isinstance(data, dict):
            raise ValueError("Invalid or missing data for the report")
        product_ids = data.get('product_ids', [])
        category_ids = data.get('category_ids', [])
        company_ids = data.get('company_ids', [])
        warehouse_ids = data.get('warehouse_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        fsn = data.get('fsn')
        if not start_date or not end_date:
            raise ValueError("Missing start_date or end_date in the data")
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
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
                            THEN CONCAT(pp.default_code, ' - ', 
                            pt.name->>'en_US')
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
        if product_ids or category_ids:
            query += " AND ("
        if product_ids:
            query += "pp.id = ANY(%s)"
            params.append(product_ids)
        if product_ids and category_ids:
            query += " OR "
        if category_ids:
            query += "pt.categ_id IN %s"
            params.append(tuple(category_ids))
        if product_ids or category_ids:
            query += ")"
        if company_ids:
            query += " AND company.id IN %s"
            params.append(tuple(company_ids))
        if warehouse_ids:
            query += " AND (COALESCE(sw_dest.id, sw_src.id) IN %s)"
            params.append(tuple(warehouse_ids))
        query += """
                GROUP BY pp.id, pt.categ_id,
                CASE
                    WHEN pp.default_code IS NOT NULL 
                        THEN CONCAT(pp.default_code, ' - ', 
                        pt.name->>'en_US')
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
        return {
            'doc_ids': docids,
            'doc_model':
                'report.inventory_advanced_reports.report_inventory_fsn',
            'data': values,
            'options': result_data if fsn == 'All' else filtered_product_stock,
        }
