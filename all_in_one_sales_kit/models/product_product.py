# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    """Inherits product.product."""
    _inherit = "product.product"

    order_partner_id = fields.Many2one(
        'res.partner', string="Partner", help="Current Partner")

    def action_sale_product_prices(self):
        """It is to show to product history."""
        rel_view_id = self.env.ref(
            'all_in_one_sales_kit.sale_order_line_view_tree')
        if self.order_partner_id.id:
            sale_lines = self.env['sale.order.line'].search(
                [('product_id', '=', self.id),
                 ('order_partner_id', '=', self.order_partner_id.id)],
                order='create_date DESC').ids
        else:
            sale_lines = self.env['sale.order.line'].search(
                [('product_id', '=', self.id)],
                order='create_date DESC').ids
        if not sale_lines:
            raise UserError("No sales history found.!")
        else:
            return {
                'domain': [('id', 'in', sale_lines)],
                'views': [(rel_view_id.id, 'tree')],
                'name': 'Sales History',
                'res_model': 'sale.order.line',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }

    def action_add_quotation(self):
        """It is a button function on clicking the product is entered to
         the order line."""
        order_id = self.env.context.get('order_id')
        list = self.env['sale.order.line'].search(
            [('order_id', '=', order_id)]).mapped('product_id')
        if self in list:
            order_line_id = self.env['sale.order.line'].search(
                [('order_id', '=', order_id), ('product_id', '=', self.id)])
            order_line_id.product_uom_qty += 1
        else:
            self.env['sale.order.line'].create({
                'product_id': self.id,
                'order_id': order_id,
                'qty_available': self.qty_available,
                'forecast_quantity': self.virtual_available,
            })
