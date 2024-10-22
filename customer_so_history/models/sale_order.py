# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_details_ids = fields.One2many('order.history.line', 'order_id')

    @api.onchange('partner_id')
    def sale_order_domain(self):
        """
         Updates the sale order lines based on the selected partner.

         This method is triggered when the `partner_id` field changes. If a partner is selected,
         it searches for all sale order lines associated with the partner's completed or confirmed
         sale orders ('sale' or 'done' states). It then creates new lines based on the retrieved
         sale orders and updates the `order_details_ids` field with these new lines.

         If no partner is selected, it clears the `order_details_ids` field.

         Fields Updated:
         - order_details_ids: A list of order lines (product, quantity, unit price, tax, and subtotal)
                              associated with the partner's completed or confirmed orders.

         Behavior:
         - Adds new order lines when a partner is selected.
         - Clears the order details if no partner is selected.

         """
        if self.partner_id:
            new_lines = []
            lines = self.env['sale.order.line'].search(
                [('order_id.partner_id', '=', self.partner_id.id),
                 ('order_id.state', 'in', ('sale', 'done'))])
            for rec in lines:
                new_lines.append(fields.Command.create({
                    'name': rec.order_id.name,
                    'product_id': rec.product_id,
                    'product_uom_qty': rec.product_uom_qty,
                    'price_unit': rec.price_unit,
                    'tax_id': [
                        fields.Command.set([line.id for line in rec.tax_id])],
                    'price_subtotal': rec.price_subtotal
                }))
            self.write({'order_details_ids': new_lines})
        else:
            self.write({'order_details_ids': [fields.Command.clear()]})
