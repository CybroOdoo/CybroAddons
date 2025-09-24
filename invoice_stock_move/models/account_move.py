# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anzil K A (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherits 'account move' to show stock picking in invoice"""
    _inherit = 'account.move'

    picking_count = fields.Integer(string="Count", copy=False,
                                   help="Count of the created picking")
    invoice_picking_id = fields.Many2one(comodel_name='stock.picking',
                                         string="Picking Id", copy=False,
                                         help="Corresponding picking")
    picking_type_id = fields.Many2one(comodel_name='stock.picking.type',
                                      string='Picking Type',
                                      compute='_compute_picking_type_id',
                                      help="This will determine the picking type "
                                           "of incoming/outgoing shipment")
    @api.depends('move_type')
    def _compute_picking_type_id(self):
        for rec in self:
            type = ''
            data = self.env['stock.picking.type'].search([])
            if self._context.get('default_move_type') == 'out_invoice':
                for line in data:
                    if line.code == 'outgoing':
                        type = line
            if self._context.get('default_move_type') == 'in_invoice':
                for line in data:
                    if line.code == 'incoming':
                        type = line
            rec.picking_type_id = type

    def action_stock_move(self):
        """Create or link a stock picking from the invoice for deliveries or credit note returns."""
        for invoice in self:
            # Determine picking type
            if invoice.move_type == 'out_refund':
                # Credit note → use incoming picking type
                picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'incoming')], limit=1)
                if not picking_type:
                    raise UserError(
                        _("No incoming picking type configured. Please configure one."))
            else:
                # Customer invoice → use outgoing picking type
                picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'outgoing')], limit=1)
                if not picking_type:
                    raise UserError(
                        _("No outgoing picking type configured. Please configure one."))

            invoice.picking_type_id = picking_type

            # Create picking if it does not exist
            if not invoice.invoice_picking_id:
                picking_vals = {
                    'picking_type_id': picking_type.id,
                    'partner_id': invoice.partner_id.id,
                    'origin': invoice.name,
                    'move_type': 'direct',
                }

                # Set locations based on picking type
                if picking_type.code == 'outgoing':
                    picking_vals.update({
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': invoice.partner_id.property_stock_customer.id,
                    })
                else:  # incoming
                    picking_vals.update({
                        'location_id': invoice.partner_id.property_stock_customer.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                    })

                picking = self.env['stock.picking'].create(picking_vals)
                invoice.invoice_picking_id = picking.id
                invoice.picking_count = 1

                # Create stock moves for stockable and consumable products
                stock_lines = invoice.invoice_line_ids.filtered(
                    lambda l: l.product_id.type in ['product', 'consu'])
                for line in stock_lines:
                    self.env['stock.move'].create({
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.quantity,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_id': picking.id,
                        'location_id': picking_vals['location_id'],
                        'location_dest_id': picking_vals['location_dest_id'],
                    })

                # Confirm and assign the picking
                picking.action_confirm()
                picking.action_assign()

            # For credit notes, create a separate return picking
            if invoice.move_type == 'out_refund':
                original_picking = invoice.invoice_picking_id

                # Create a new incoming picking for the return
                return_picking = self.env['stock.picking'].create({
                    'origin': invoice.name,
                    'picking_type_id': picking_type.id,
                    'location_id': invoice.partner_id.property_stock_customer.id,
                    # source = customer
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    # dest = stock
                    'partner_id': invoice.partner_id.id,
                    'move_type': 'direct',
                })

                # Create stock moves for returned products
                for line in invoice.invoice_line_ids.filtered(
                        lambda l: l.product_id.type in ['product', 'consu']):
                    self.env['stock.move'].create({
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.quantity,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_id': return_picking.id,
                        'location_id': invoice.partner_id.property_stock_customer.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                    })

                # Confirm and assign the return picking
                return_picking.action_confirm()
                return_picking.action_assign()

                # Link the return picking to the credit note
                invoice.invoice_picking_id = return_picking.id

    def action_view_picking(self):
        """Function to view moves while clicking shipment smart button"""
        action = self.env.ref('stock.action_picking_tree_ready')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        result['domain'] = [('id', '=', self.invoice_picking_id.id)]
        pick_ids = sum([self.invoice_picking_id.id])
        if pick_ids:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids or False
        return result

    def _reverse_moves(self, default_values_list=None, cancel=False):
        """ Reverse a recordset of account.move.
            If cancel parameter is true, the reconcilable or liquidity lines
            of each original move will be reconciled with its reverse's.
            :param default_values_list: A list of default values to consider per
             move. ('type' & 'reversed_entry_id' are computed in the method).
            :return: An account move recordset, reverse of the current self."""
        if self.picking_type_id.code == 'outgoing':
            data = self.env['stock.picking.type'].search(
                [('company_id', '=', self.company_id.id),
                 ('code', '=', 'incoming')], limit=1)
            self.picking_type_id = data.id
        elif self.picking_type_id.code == 'incoming':
            data = self.env['stock.picking.type'].search(
                [('company_id', '=', self.company_id.id),
                 ('code', '=', 'outgoing')], limit=1)
            self.picking_type_id = data.id
        return super(AccountMove, self)._reverse_moves()
