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
from odoo import api, fields, models


class SaleOrder(models.Model):
    """Extends the sale order with the customer's order history."""

    _inherit = 'sale.order'

    order_details_ids = fields.One2many(
        'order.history.line', 'order_id', string='Order History',
        help="Previous order lines of the selected customer.")

    @api.onchange('partner_id')
    def _onchange_partner_id_order_history(self):
        """Load the customer's previous confirmed and done order lines."""
        if not self.partner_id:
            self.order_details_ids = [fields.Command.clear()]
            return
        lines = self.env['sale.order.line'].search([
            ('order_id.partner_id', '=', self.partner_id.id),
            ('order_id.state', 'in', ('sale', 'done')),
        ])
        self.order_details_ids = [fields.Command.clear()] + [
            fields.Command.create({
                'name': line.order_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'tax_id': [fields.Command.set(line.tax_ids.ids)],
                'price_subtotal': line.price_subtotal,
            }) for line in lines
        ]
