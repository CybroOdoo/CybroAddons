# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    """Inherit model and add fields and methods"""
    _inherit = "product.product"

    order_partner_id = fields.Many2one(
        'res.partner', string="Partner", help="Choose partner"
    )

    def action_purchase_product_prices(self):
        """Display the purchase history of a product."""
        rel_view_id = self.env.ref(
            'all_in_one_purchase_kit.last_product_purchase_prices_view')
        if self.order_partner_id.id:
            purchase_lines = self.env['purchase.order.line'].search(
                [('product_id', '=', self.id),
                 ('partner_id', '=', self.order_partner_id.id)],
                order='create_date DESC').mapped('id')
        else:
            purchase_lines = self.env['purchase.order.line'].search(
                [('product_id', '=', self.id)],
                order='create_date DESC').mapped('id')
        if not purchase_lines:
            raise UserError("No purchase history found.!")
        return {
            'domain': [('id', 'in', purchase_lines)],
            'views': [(rel_view_id.id, 'tree')],
            'name': 'Purchase History',
            'res_model': 'purchase.order.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

    @api.model
    def most_purchased_product(self):
        """Method returns most purchased products"""
        purchased_qty = self.search_read([], ['name', 'purchased_product_qty'])
        product_qty = {count['name']: count['purchased_product_qty'] for count
                       in purchased_qty if count['purchased_product_qty'] > 0}
        sorted_qty = {key: val for key, val in sorted(
            product_qty.items(), key=lambda ele: ele[1], reverse=True)
                      }
        return {'purchased_qty': sorted_qty}

    def add_to_rfq(self):
        """When click on add to RFQ button product added to RFQ"""
        order_id = self.env.context.get('order_id')
        sale_order_id = self.env['purchase.order.line'].search(
            [('order_id', '=', order_id)])
        lst = [rec.product_id for rec in sale_order_id]
        if self in lst:
            order_line_id = self.env['purchase.order.line'].search(
                [('order_id', '=', order_id), ('product_id', '=', self.id)])
            order_line_id.product_uom_qty += 1
        else:
            self.env['purchase.order.line'].create({
                'product_id': self.id,
                'order_id': order_id,
            })
