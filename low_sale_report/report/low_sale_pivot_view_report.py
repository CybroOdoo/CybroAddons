# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class LowSalePivotViewReport(models.Model):
    """Pivot view report"""
    _name = 'low.sale.pivot.view.report'
    _description = 'LowSale Pivot View Report'

    categ_id = fields.Many2one(
        comodel_name='product.category', string="Product Category",
        readonly=True, help='Category  id of the product')
    product_id = fields.Many2one(
        comodel_name='product.product', string="Product Variant", readonly=True,
        help='Product_product model id')
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template', string="Product", readonly=True,
        help='Product_template model id')
    product_uom_qty = fields.Float(string="Sold quantity", readonly=True,
                                   help='Total count of the quantity to sold')
    company_id = fields.Many2one(comodel_name='res.company', store=True,
                                 copy=False, string="Company",
                                 default=lambda
                                 self: self.env.user.company_id.id,
                                 help='Company id for the reference of the'
                                      ' monetary field')
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda
                                  self: self.env.user.company_id.currency_id.id,
                                  help='Currency id for the reference of the '
                                       'monetary field')
    price_total = fields.Monetary(string="Total", readonly=True,
                                  help='Total price of the product sold')

    def get_data(self, low_sale_report):
        """Fetching the data for the pivot view and the Excel report using
         the sql query"""
        conditions = []
        filters = []
        if low_sale_report['analysed_period_start'] and low_sale_report[
                           'analysed_period_end']:
            filters.append(f"o.date_order BETWEEN '"
                           f"{low_sale_report['analysed_period_start']}"
                           f"' AND '"
                           f"{low_sale_report['analysed_period_end']}'")
        if low_sale_report['absolute_qty'] > 0:
            conditions.append(
                f"COALESCE(SUM(CASE WHEN o.state = 'sale' THEN "
                f"l.product_uom_qty ELSE 0 END), 0) <= "
                f"{low_sale_report['absolute_qty']}")
        if low_sale_report['category']:
            filters.append(
                "t.categ_id = %s" % int(low_sale_report['category'][0]))
        if low_sale_report['sale_team']:
            filters.append(
                "o.team_id = %s" % int(low_sale_report['sale_team'][0]))
        if low_sale_report['product_type'] == 'variant':
            query = """
                        SELECT
                            p.id AS product_id,
                            COALESCE(SUM(CASE WHEN o.state = 'sale' THEN 
                            l.product_uom_qty ELSE 0 END), 0) AS 
                            total_sold_quantity,
                            COALESCE(SUM(CASE WHEN o.state = 'sale' THEN 
                            l.price_total ELSE 0 END), 0) AS price_total,
                            t.name->>'en_US' AS product_name
                        FROM
                            product_product p
                        LEFT JOIN
                            product_template t ON p.product_tmpl_id = t.id    
                        LEFT JOIN
                            sale_order_line l ON p.id = l.product_id
                        LEFT JOIN
                            sale_order o ON l.order_id = o.id
                        """ + ('WHERE ' + ' AND '.join(filters) if
                               filters else '') + """    
                        GROUP BY
                            p.id, t.name
                        """ + ('HAVING ' + ' AND '.join(conditions) if
                               conditions else '') + """    
                    """
        else:
            query = """
                        SELECT
                            t.id AS product_tmpl_id,
                            COALESCE(SUM(CASE WHEN o.state = 'sale' THEN 
                            l.product_uom_qty ELSE 0 END), 0) AS 
                            total_sold_quantity,
                            COALESCE(SUM(CASE WHEN o.state = 'sale' THEN 
                            l.price_total ELSE 0 END), 0) AS price_total,
                            t.name->>'en_US' AS product_name
                        FROM
                            product_template t
                        LEFT JOIN
                            product_product p ON t.id = p.product_tmpl_id
                        LEFT JOIN
                            sale_order_line l ON p.id = l.product_id
                        LEFT JOIN
                            sale_order o ON l.order_id = o.id
                        """ + ('WHERE ' + ' AND '.join(filters) if
                               filters else '') + """     
                        GROUP BY
                            t.id, t.name
                        """ + ('HAVING ' + ' AND '.join(conditions) if
                               conditions else '') + """      
                    """
        self.env.cr.execute(query)
        test = self.env.cr.fetchall()
        return test
