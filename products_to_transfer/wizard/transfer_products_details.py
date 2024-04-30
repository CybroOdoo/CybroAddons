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
from datetime import timedelta
from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError


class TransferProductDetails(models.TransientModel):
    """This wizard is designed to display product details associated with
    inventory transfers.It provides information about the transferred product,
    its quantity, associated picking, and transfer history."""
    _name = 'transfer.products.details'
    _description = 'Wizard to View Product Details from Inventory Transfer'

    def _default_picking(self):
        """Get the default picking name based on the context value
         'picking_id'."""
        picking_id = self.env['stock.picking'].browse(
            self._context.get('picking_id'))
        return picking_id.name

    product = fields.Char(string="Product", readonly=True,
                          help="The product associated with the transfer")
    qty = fields.Float(string="Quantity",
                       help="The quantity of the product transferred")
    picking = fields.Char(string="Picking", readonly=True,
                          default=_default_picking,
                          help="The picking associated with the transfer")
    transfer_history_ids = fields.One2many('product.transfer.history',
                                           'product_details_id',
                                           string="Transfer History",
                                           readonly=True,
                                           help="The transfer history records "
                                                "associated with the product")
    date_from = fields.Date(string="Transfer History From",
                            default=fields.Date.today() - timedelta(days=30),
                            required=True,
                            help="The starting date for the transfer history")

    @api.onchange('date_from')
    def _onchange_date_from(self):
        """Update transfer history based on the selected date."""
        move_ids = self.env['stock.move'].sudo().search([
            ('product_id', '=', self._context.get('active_id')),
            ('state', '=', 'done'),
            ('picking_id.date_done', '>=', self.date_from)])
        vals = [Command.create({
            'date_picking': move.date,
            'partner_id': move.picking_id.partner_id.id,
            'qty': move.product_uom_qty,
            'picking': move.picking_id.name
        }) for move in move_ids]
        self.transfer_history_ids = vals

    def action_add_to_transfer(self):
        """Add the product to the inventory transfer."""
        picking_id = self.env['stock.picking'].browse(
            self._context.get('picking_id'))
        product_id = self.env['product.product'].browse(
            self._context.get('active_id'))
        if not picking_id:
            raise ValidationError(
                _("There are no active transfers. unable to add product."))
        display_name = product_id.name_get()[0][1]
        if product_id.description_sale:
            display_name += '\n' + product_id.description_sale
        move_vals = {
            'product_id': product_id.id,
            'name': display_name,
            'product_uom_qty': self.qty,
            'product_uom': product_id.uom_id.id,
            'location_id': picking_id.location_id.id,
            'location_dest_id': picking_id.location_dest_id.id,
            'picking_id': picking_id.id}
        existing_move = self.env['stock.move'].search([
            ('picking_id', '=', picking_id.id),
            ('product_id', '=', product_id.id)])
        if existing_move:
            existing_move[0].product_uom_qty += self.qty
        else:
            self.env['stock.move'].create(move_vals)
