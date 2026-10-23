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
from odoo import _, Command, models


class ProductProduct(models.Model):
    """This class extends the 'product.product' model to enhance its
       functionality. It adds features for adding the current product to a
       stock picking and viewing product details in transfer.products.details
       model."""
    _inherit = 'product.product'

    def action_add_to_picking(self):
        """Add the current product to the stock picking."""
        self.ensure_one()
        picking_id = self.env['stock.picking'].browse(
            self.env.context.get('picking_id') or self.env.context.get('active_id')
        )
        if not picking_id or picking_id._name != 'stock.picking' or not picking_id.exists():
            return {
                'type': 'ir.actions.act_window',
                'name': _('Add Product to Draft Picking'),
                'res_model': 'wizard.add.to.draft.picking',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_product_id': self.id,
                },
            }

        existing_move = picking_id.move_ids.filtered(
            lambda move: move.product_id == self
        )
        if existing_move:
            existing_move[0].product_uom_qty += 1
        else:
            picking_id.write({
                'move_ids': [Command.create({
                    'reference': self.name,
                    'product_id': self.id,
                    'uom_id': self.uom_id.id,
                    'product_uom_qty': 1,
                    'location_id': picking_id.location_id.id,
                    'location_dest_id': picking_id.location_dest_id.id,
                })],
            })

    def action_view_details(self):
        """Open a new window to display product details."""
        self.ensure_one()
        picking_id = self.env['stock.picking'].browse(
            self.env.context.get('picking_id') or self.env.context.get('active_id')
        )
        target_picking_id = (
            picking_id.id
            if picking_id and picking_id._name == 'stock.picking' and picking_id.exists()
            else False
        )
        return {
            'name': _('Product Details'),
            'view_mode': 'form',
            'res_model': 'transfer.products.details',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_picking_id': target_picking_id,
                'default_product_id': self.id,
            },
        }
