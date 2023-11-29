# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class PosOrder(models.Model):
    """Get details from pos order"""
    _inherit = 'pos.order'

    def get_category_summary(self, order_ids):
        """Function to get category details"""
        categories = []
        if order_ids:
            self.env.cr.execute("""SELECT category.name,category.id, 
            sum(price_subtotal_incl) as amount, 
                sum(qty) as qty FROM pos_order_line AS line INNER JOIN
                product_product AS product ON 
                line.product_id = product.id INNER JOIN
                product_template AS template ON 
                product.product_tmpl_id = template.id 
                INNER JOIN pos_category as category ON 
                template.pos_categ_id = category.id 
                WHERE line.order_id IN %s GROUP BY 
                category.name,category.id """,
                                (tuple(order_ids),))
            categories = self.env.cr.dictfetchall()
        return categories

    def get_product_summary(self, order_ids):
        """Function to get product details"""
        product_summary = []
        if order_ids:
            self.env.cr.execute("""
                SELECT product.id, template.name, product.default_code as code,
                 sum(qty) as qty
                FROM product_product AS product,
                     pos_order_line AS line, product_template AS template
                WHERE product.id = line.product_id AND 
                template.id = product.product_tmpl_id
                    AND line.order_id IN %s
                GROUP BY product.id, template.name, template.default_code
            """, (tuple(order_ids),))
            product_summary = self.env.cr.dictfetchall()
        return product_summary

    def get_order_summary(self, order_ids):
        """Function to get order details"""
        orders = self.env["pos.order"].browse(order_ids)
        order_summary = []
        for order in orders:
            order_summary.append(
                {'order_name': order.name,
                 'state': dict(self._fields['state'].selection).get(
                     order.state),
                 'date_order': order.date_order,
                 'amount_total': order.amount_total})
        return order_summary
