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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockTransfer(models.TransientModel):
    """Model for managing internal stock transfers between locations."""
    _name = 'stock.transfer'
    _description = "Stock Transfer"

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='Product to transfer.'
    )

    qty_available = fields.Float(
        string='Available Quantity',
        help="Available quantity of the selected product.",
        related="product_id.qty_available",
        readonly=True
    )

    qty_to_move = fields.Float(
        string='Quantity to Move',
        help="Quantity of product to transfer."
    )

    location_ids = fields.Many2many(
        'stock.location',
        string='Locations',
        help="Available locations containing the selected product."
    )

    source_location_id = fields.Many2one(
        'stock.location',
        domain="[('id', 'in', location_ids)]",
        required=True,
        string='Source Location',
        help='Location to transfer product from.'
    )

    destination_location_id = fields.Many2one(
        'stock.location',
        domain="[('usage', '=', 'internal')]",
        required=True,
        string='Destination Location',
        help='Location to transfer product to.'
    )

    @api.onchange('product_id')
    def _onchange_product(self):
        """Update internal locations containing the selected product."""
        for rec in self:
            if rec.product_id:
                stock_quants = self.env['stock.quant'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('on_hand', '=', True),
                    ('quantity', '>', 0)
                ])
                locations = stock_quants.mapped('location_id')
                rec.location_ids = [(6, 0, locations.ids)]

    def create_action(self):
        """Create and validate an internal stock transfer."""
        self.ensure_one()

        if self.qty_to_move > self.qty_available:
            raise UserError(_(
                'Quantity to move must be less than or equal to available quantity.'
            ))
        operation_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.source_location_id.warehouse_id.id)
        ], limit=1)

        if not operation_type:
            raise UserError(_(
                'No internal operation type found for the selected source warehouse.'
            ))
        stock_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.source_location_id.id),
            ('quantity', '>=', self.qty_to_move)
        ], limit=1)

        if not stock_quant:
            raise UserError(_(
                'No sufficient quantity available for this product in the selected source location.'
            ))

        picking_vals = {
            'picking_type_id': operation_type.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'scheduled_date': fields.Datetime.now(),
        }
        picking = self.env['stock.picking'].sudo().create(picking_vals)

        move_vals = {
            'name': self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.qty_to_move,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'product_uom': self.product_id.uom_id.id,
            'picking_id': picking.id,
        }
        self.env['stock.move'].sudo().create(move_vals)

        picking.action_confirm()
        picking.sudo().button_validate()

        return {
            'type': 'ir.actions.act_window',
            'target': 'current',
            'name': _("Stock Transfer"),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': picking.id,
        }

