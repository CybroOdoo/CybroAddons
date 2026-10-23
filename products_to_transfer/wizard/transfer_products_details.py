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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta

from odoo import _, Command, api, fields, models
from odoo.exceptions import ValidationError


class TransferProductDetails(models.TransientModel):
    """This wizard is designed to display product details associated with
    inventory transfers. It provides information about the transferred product,
    its quantity, associated picking, and transfer history."""
    _name = 'transfer.products.details'
    _description = 'Wizard to View Product Details from Inventory Transfer'

    def _default_product_id(self):
        """Get the default product based on product_id or active_id in context."""
        ctx = self.env.context
        prod_id = ctx.get('default_product_id') or ctx.get('product_id')
        if not prod_id and ctx.get('active_model') == 'product.product':
            prod_id = ctx.get('active_id')
        if prod_id:
            product = self.env['product.product'].browse(prod_id)
            if product.exists():
                return product.id
        return False

    def _default_picking_id(self):
        """Get the default picking based on picking_id or active_id in context."""
        ctx = self.env.context
        pick_id = ctx.get('default_picking_id') or ctx.get('picking_id')
        if not pick_id and ctx.get('active_model') == 'stock.picking':
            pick_id = ctx.get('active_id')
        if pick_id:
            picking = self.env['stock.picking'].browse(pick_id)
            if picking.exists():
                return picking.id
        return False

    product_id = fields.Many2one(
        'product.product', string="Product", required=True,
        default=_default_product_id,
        help="The product associated with the transfer"
    )
    qty = fields.Float(
        string="Quantity", default=1.0,
        help="The quantity of the product to transfer"
    )
    picking_id = fields.Many2one(
        'stock.picking', string="Picking", required=True,
        domain="[('state', '=', 'draft')]",
        default=_default_picking_id,
        help="The picking associated with the transfer"
    )
    transfer_history_ids = fields.One2many(
        'product.transfer.history', 'product_details_id',
        string="Transfer History", readonly=True,
        help="The transfer history records associated with the product"
    )
    date_from = fields.Date(
        string="Transfer History From",
        default=lambda self: fields.Date.today() - timedelta(days=30),
        required=True,
        help="The starting date for the transfer history"
    )

    @api.onchange('date_from', 'product_id')
    def _onchange_date_from(self):
        """Update transfer history based on the selected date and product."""
        if not self.product_id or not self.date_from:
            self.transfer_history_ids = [Command.clear()]
            return
        move_ids = self.env['stock.move'].sudo().search([
            ('product_id', '=', self.product_id.id),
            ('state', '=', 'done'),
            ('picking_id.date_done', '>=', self.date_from),
        ])
        vals = [Command.create({
            'date_picking': move.date,
            'partner_id': move.picking_id.partner_id.id,
            'qty': move.product_uom_qty,
            'picking': move.picking_id.name,
        }) for move in move_ids]
        self.transfer_history_ids = [Command.clear()] + vals

    def action_add_to_transfer(self):
        """Add the product to the inventory transfer."""
        self.ensure_one()
        picking_id = self.picking_id
        product_id = self.product_id
        if not picking_id:
            raise ValidationError(
                _("There are no active transfers. Unable to add product.")
            )
        display_name = product_id.display_name
        if product_id.description_sale:
            display_name += '\n' + product_id.description_sale
        move_vals = {
            'product_id': product_id.id,
            'reference': display_name,
            'product_uom_qty': self.qty,
            'uom_id': product_id.uom_id.id,
            'location_id': picking_id.location_id.id,
            'location_dest_id': picking_id.location_dest_id.id,
            'picking_id': picking_id.id,
        }
        existing_move = self.env['stock.move'].search([
            ('picking_id', '=', picking_id.id),
            ('product_id', '=', product_id.id),
        ])
        if existing_move:
            existing_move[0].product_uom_qty += self.qty
        else:
            self.env['stock.move'].create(move_vals)
