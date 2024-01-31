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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AgingReport(models.AbstractModel):
    """Create an abstract model for passing reporting values"""
    _name = 'report.inventory_advanced_reports.report_inventory_aging'
    _description = 'Aging Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """This function has working in get the pdf report."""
        values = data
        product_ids = data['product_ids']
        category_ids = data['category_ids']
        company_ids = data['company_ids']
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
                    LEFT JOIN stock_picking_type spt ON 
                    sm.picking_type_id = spt.id
                    LEFT JOIN res_company company ON sm.company_id = company.id
                    INNER JOIN stock_valuation_layer svl ON 
                    svl.stock_move_id = sm.id
                    WHERE pt.detailed_type = 'product'
                    AND sm.state = 'done'
                                    """
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
            query += " AND (sm.company_id = ANY(%s))"
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
        today = fields.datetime.now().date()
        for row in result_data:
            receipt_date = row.get('receipt_date')
            if receipt_date:
                receipt_date = receipt_date.date()
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
            return {
                'doc_ids': docids,
                'doc_model':
                    'report.inventory_advanced_reports.report_inventory_aging',
                'data': values,
                'options': result_data,
            }
        else:
            raise ValidationError("No records found for the given criteria!")
