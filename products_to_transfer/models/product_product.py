# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
from odoo import Command, models, _
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    """This class extends the 'product.product' model to enhance its
       functionality. It adds features for adding the current product to a
       stock picking and viewing product details in transfer.products.details
        model."""
    _inherit = 'product.product'

    def action_add_to_picking(self):
        """Add the current product to the stock picking."""
        self.ensure_one()
        if not self._context.get('active_id'):
            raise ValidationError(
                _("There are no current stock picks available. Unable to add "
                  "product."))
        picking_id = self.env['stock.picking'].browse(
            self._context.get('active_id'))
        existing_move = picking_id.move_ids_without_package.filtered(
            lambda move: move.product_id == self)
        if existing_move:
            existing_move[0].product_uom_qty += 1
        else:
            picking_id.write({
                'move_ids_without_package': [Command.create(
                    {'name': self.name,
                     'product_id': self.id,
                     'product_uom': self.uom_id.id,
                     'product_uom_qty': 1,
                     'location_id': picking_id.location_id.id,
                     'location_dest_id': picking_id.location_dest_id.id, })],
            })

    def action_view_details(self):
        """Open a new window to display product details."""
        return {
            'name': 'Product Details',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'transfer.products.details',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'picking_id': self.env['stock.picking'].browse(
                    self._context.get('active_id')).id,
                'default_product': self.name,
            }
        }
