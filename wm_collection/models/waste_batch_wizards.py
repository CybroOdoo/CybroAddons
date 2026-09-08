# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class WasteBatchTransferWizard(models.TransientModel):
    """Wizard to execute internal stock location transfers for received waste batches."""
    _name = 'waste.batch.transfer.wizard'
    _description = 'Transfer Waste Batch to Another Location'

    batch_id = fields.Many2one('waste.batch', string='Batch', required=True, readonly=True)
    source_location_id = fields.Many2one('stock.location', string='From Location', readonly=True)
    dest_location_id = fields.Many2one(
        'stock.location',
        string='To Location',
        required=True,
        domain="[('usage', '=', 'internal'), ('id', '!=', source_location_id)]",
    )
    notes = fields.Text(string='Transfer Notes')

    def action_confirm_transfer(self):
        """
        Confirm the stock transfer proposed in the waste batch transfer wizard,
        creating and validating the corresponding Odoo stock picking to move
        materials between locations.
        """
        self.ensure_one()
        batch = self.batch_id
        if not batch.is_received:
            raise UserError(_("Only received batches can be transferred."))
        if self.dest_location_id == batch.location_id:
            raise UserError(_("Source and destination locations are the same."))

        int_type = batch.warehouse_id.int_type_id
        if not int_type:
            int_type = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', batch.warehouse_id.id),
                ('code', '=', 'internal'),
            ], limit=1)

        picking = self.env['stock.picking'].create({
            'picking_type_id': int_type.id if int_type else False,
            'location_id': batch.location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'origin': batch.name,
            'company_id': batch.warehouse_id.company_id.id or self.env.company.id,
        })

        moves = self.env['stock.move']
        for line in batch.line_ids:
            if line.quantity <= 0:
                continue
            move = self.env['stock.move'].create({
                'product_id': line.product_id.id,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.quantity,
                'location_id': batch.location_id.id,
                'location_dest_id': self.dest_location_id.id,
                'picking_id': picking.id,
                'origin': batch.name,
                'company_id': batch.warehouse_id.company_id.id or self.env.company.id,
            })
            moves |= move

        picking.action_confirm()
        picking.action_assign()

        for move in moves:
            # Find the corresponding batch line
            line = batch.line_ids.filtered(lambda l: l.product_id.id == move.product_id.id)
            if not line:
                continue
            qty = line[0].quantity
            lot_id = line[0].lot_id.id
            for ml in move.move_line_ids:
                ml.lot_id = lot_id
                ml.quantity = qty
            if not move.move_line_ids:
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': qty,
                    'location_id': batch.location_id.id,
                    'location_dest_id': self.dest_location_id.id,
                    'lot_id': lot_id,
                    'company_id': batch.warehouse_id.company_id.id or self.env.company.id,
                })

        picking.button_validate()

        batch.write({'location_id': self.dest_location_id.id})

        batch.message_post(body=_(
            "Transferred batch to %(loc)s.%(notes)s",
            loc=self.dest_location_id.complete_name,
            notes=(' Notes: ' + self.notes) if self.notes else '',
        ))
        return {'type': 'ir.actions.act_window_close'}
