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
    """POS Order model inheritance.

    Automatically triggers the creation and optional completion of
    Manufacturing Orders (MRP) for order lines containing products configured
    for automated manufacturing.
    """
    _inherit = 'pos.order'

    @api.model
    def _process_order(self, order, existing_order):
        """Override _process_order to create MRP orders if needed."""
        pos_order_id = super()._process_order(order, existing_order)
        if pos_order_id:
            pos_order = self.browse(pos_order_id)
            pos_order.create_mrp_orders()
        return pos_order_id

    def create_mrp_orders(self):
        """Logic to create MRP orders from POS order lines."""
        mrp_orders = self.env['mrp.production']
        for order in self:
            for line in order.lines:
                product = line.product_id
                if product.to_create_mrp and line.qty > 0:
                    bom = self.env['mrp.bom']._bom_find(
                        product, company_id=order.company_id.id
                    )[product]
                    if bom:
                        mrp_vals = {
                            'product_id': product.id,
                            'product_qty': line.qty,
                            'bom_id': bom.id,
                            'origin': order.name,
                            'company_id': order.company_id.id,
                            'date_start': order.date_order,
                        }
                        mrp_order = self.env['mrp.production'].create(mrp_vals)
                        mrp_order.action_confirm()
                        if product.create_mrp_done:
                            mrp_order.button_mark_done()
                        mrp_orders |= mrp_order
        return mrp_orders
