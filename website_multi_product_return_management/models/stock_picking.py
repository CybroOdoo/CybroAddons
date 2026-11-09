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
from odoo import fields, models


class StockPicking(models.Model):
    """Extend the stock.picking model to include return order information."""
    _inherit = 'stock.picking'

    return_order_id = fields.Many2one(
        'sale.return', string='Return Order',
        help="Shows the return order of the current transfer.")
    return_order_pick_id = fields.Many2one(
        'sale.return',
        string='Return Order Pick',
        help="Shows the return order picking of the current return order.")
    return_order_picking = fields.Boolean(
        string='Return Order Picking',
        help="Helps to identify delivery and return picking. If true, the "
             "transfer is a return picking; else, it's a delivery.")

    def button_validate(self):
        """Override the button_validate method to update return order state."""
        res = super().button_validate()
        for rec in self:
            if rec.return_order_pick_id:
                if any(line.state != 'done' for line in
                       rec.return_order_pick_id.stock_picking_ids):
                    return res
                else:
                    rec.return_order_pick_id.write({'state': 'done'})
        return res
