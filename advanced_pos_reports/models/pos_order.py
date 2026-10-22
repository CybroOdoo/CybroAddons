# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, models


class PosOrder(models.Model):
    """Get details from pos order"""
    _inherit = 'pos.order'

    @api.model
    def get_category_summary(self, order_ids):
        """Function to get category details"""
        categories = []
        if order_ids:
            self.env.cr.execute("""
                SELECT category.name, category.id,
                       sum(line.price_subtotal_incl) AS amount,
                       sum(line.qty) AS qty
                FROM pos_order_line AS line
                INNER JOIN product_product AS product ON line.product_id = product.id
                INNER JOIN product_template AS template ON product.product_tmpl_id = template.id
                INNER JOIN pos_category_product_template_rel AS categ ON product.product_tmpl_id = categ.product_template_id
                INNER JOIN pos_category AS category ON categ.pos_category_id = category.id
                WHERE line.order_id IN %s
                GROUP BY category.name, category.id
            """, (tuple(order_ids),))
            for row in self.env.cr.dictfetchall():
                name = row['name']
                if isinstance(name, dict):
                    name = name.get(self.env.lang) or name.get('en_US') or next(iter(name.values()), '')
                row['name'] = name
                categories.append(row)
        return categories

    @api.model
    def get_product_summary(self, order_ids):
        """Function to get product details"""
        product_summary = []
        if order_ids:
            self.env.cr.execute("""
                SELECT product.id, template.name, product.default_code AS code,
                       sum(line.qty) AS qty
                FROM product_product AS product
                INNER JOIN pos_order_line AS line ON product.id = line.product_id
                INNER JOIN product_template AS template ON product.product_tmpl_id = template.id
                WHERE line.order_id IN %s
                GROUP BY product.id, template.name, product.default_code
            """, (tuple(order_ids),))
            for row in self.env.cr.dictfetchall():
                name = row['name']
                if isinstance(name, dict):
                    name = name.get(self.env.lang) or name.get('en_US') or next(iter(name.values()), '')
                row['name'] = name
                product_summary.append(row)
        return product_summary

    @api.model
    def get_order_summary(self, order_ids):
        """Function to get order details"""
        orders = self.env["pos.order"].browse(order_ids).exists()
        order_summary = []

        state_dict = dict(self._fields['state'].selection)
        for order in orders:
            order_summary.append({
                'order_name': order.name,
                'state': state_dict.get(order.state, order.state),
                'date_order': str(order.date_order.date()) if order.date_order else '',
                'amount_total': order.amount_total,
                'id': order.id,
            })
        return order_summary
