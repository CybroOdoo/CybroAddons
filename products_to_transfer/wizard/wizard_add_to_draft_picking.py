# -*- coding: utf-8 -*-
"""Wizard Add To Draft Picking Model"""
# pylint: disable=import-error, too-few-public-methods, line-too-long
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import _, Command,fields,models
from odoo.exceptions import ValidationError


class WizardAddToDraftPicking(models.TransientModel):
    """This wizard allows users to add a specified quantity of a product
        to a draft picking. It ensures that the selected picking is in the
        draft state and handles both adding new products and updating
        quantities for existing products within the picking."""
    _name = 'wizard.add.to.draft.picking'
    _description = 'Wizard to add product to draft picking'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    picking_id = fields.Many2one('stock.picking', string='Draft Picking', domain="[('state', '=', 'draft')]")
    qty = fields.Float(string='Quantity', default=1.0, required=True)

    def action_add_to_transfer(self):
        """Adds the specified quantity of the selected product to the
           selected draft picking. If the product already exists in the
           picking, its quantity is updated. If not, a new move is created
           within the picking for the product."""
        self.ensure_one()
        if not self.picking_id:
            raise ValidationError(_("Please select a draft picking."))
        existing_move = self.picking_id.move_ids.filtered(
            lambda move: move.product_id == self.product_id)
        if existing_move:
            existing_move[0].product_uom_qty += self.qty
        else:
            self.picking_id.write({
                'move_ids': [Command.create({
                    'reference': self.product_id.name,
                    'product_id': self.product_id.id,
                    'product_uom': self.product_id.uom_id.id,
                    'product_uom_qty': self.qty,
                    'location_id': self.picking_id.location_id.id,
                    'location_dest_id': self.picking_id.location_dest_id.id,
                })],
            })
