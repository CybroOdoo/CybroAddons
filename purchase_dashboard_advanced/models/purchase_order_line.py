# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models


class PurchaseOrderLine(models.Model):
    """Model representing purchase order lines and related analytics.
      Inherits from 'purchase.order.line' model."""
    _inherit = 'purchase.order.line'

    @api.model
    def product_categ_analysis(self):
        """Get product category analysis data.
         :return: Product category analysis data
         :rtype: dict"""
        company_id = self.env.user.company_id.id
        quantity_query = """
            SELECT product_template.name, SUM(pl.product_qty) as total_quantity
            FROM purchase_order_line pl
            JOIN product_product ON pl.product_id = product_product.id
            JOIN product_template ON product_product.product_tmpl_id = 
            product_template.id
            WHERE pl.company_id = %s
            GROUP BY product_template.name
        """
        self._cr.execute(quantity_query, (company_id,))
        products_quantity = self._cr.fetchall()
        if not products_quantity:  # Check if products_quantity is empty
            return {'values': {'name': [], 'count': []}, 'category_id': []}
        name, quantity_done = zip(*products_quantity)
        categories = self.get_categories()
        value = {'name': name, 'count': quantity_done}
        return {'values': value, 'category_id': categories}

    def get_categories(self):
        """Get product categories.
        :return: Product categories
        :rtype: list"""
        category_query = """
                    SELECT pc.id, pc.name
                    FROM product_category pc
                    JOIN product_template pt ON pt.categ_id = pc.id
                    JOIN product_product pp ON pp.product_tmpl_id = pt.id
                    JOIN purchase_order_line pl ON pl.product_id = pp.id
                    WHERE pl.company_id = %s
                    GROUP BY pc.id, pc.name
                """
        self._cr.execute(category_query, (self.env.user.company_id.id,))
        return self._cr.fetchall()

    @api.model
    def product_categ_data(self, args):
        """Get product category data.
        :param args: Category ID
        :type args: int
        :return: Product category data
        :rtype: dict"""
        category_id = int(args or 1)
        company_id = self.env.company.id
        query = """
            SELECT product_template.name, SUM(pl.product_qty)
            FROM purchase_order_line pl
            INNER JOIN product_product ON pl.product_id = product_product.id
            INNER JOIN product_template ON product_product.product_tmpl_id = 
            product_template.id
            WHERE pl.company_id = %s AND product_template.categ_id = %s
            GROUP BY product_template.name
        """
        self._cr.execute(query, (company_id, category_id))
        product_move = self._cr.dictfetchall()
        value = {
            'name': [record.get('name') for record in product_move],
            'count': [record.get('sum') for record in product_move],
        }
        return value
