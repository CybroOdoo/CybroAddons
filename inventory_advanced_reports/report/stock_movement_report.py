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


class StockMovementReport(models.AbstractModel):
    """Create an abstract model for passing reporting values"""
    _name = 'report.inventory_advanced_reports.report_inventory_movement'
    _description = 'Stock Movement Report'

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
        report_up_to_certain_date = data.get('report_up_to_certain_date', [])
        up_to_certain_date = data.get('up_to_certain_date', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if not start_date or not end_date:
            raise ValueError(
                "Missing start_date or end_date in the data")
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
        if report_up_to_certain_date:
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
            params = [up_to_certain_date] * 15
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
            params = [start_date, start_date, end_date, end_date] + [start_date, end_date] * 12
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
        if product_ids:
            product_ids = [product_id for product_id in product_ids]
            query += " AND pp.id = ANY(%s)"
            params.append(product_ids)
        if category_ids:
            category_ids = [category for category in category_ids]
            query += " AND (pt.categ_id = ANY(%s))"
            params.append(category_ids)
        if company_ids:
            company_ids = [company for company in company_ids]
            query += " AND sm.company_id = ANY(%s)"
            params.append(company_ids)
        if warehouse_ids:
            warehouse_ids = [warehouse for warehouse in warehouse_ids]
            query += " AND (COALESCE(sw_dest.id, sw_src.id) = ANY(%s))"
            params.append(warehouse_ids)
        query += """
            GROUP BY pp.id, pt.name, pc.complete_name, company.name
        """
        self.env.cr.execute(query, params)
        result_data = self.env.cr.dictfetchall()
        if result_data:
            return {
                'doc_ids': docids,
                'doc_model': 'inventory.overstock.report',
                'data': values,
                'options': result_data,
            }
        else:
            raise ValidationError("No records found for the given criteria!")
