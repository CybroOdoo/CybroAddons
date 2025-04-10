# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
from odoo import fields, models, _, api
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
                                      compute='compute_stock_type',
                                      store=True, readonly=False,
                                      help="This will determine the picking type "
                                           "of incoming/outgoing shipment")

    @api.depends('move_type')
    def compute_stock_type(self):
        """Computes the picking type based on the move type."""
        for rec in self:
            rec.picking_type_id = False
            picking_types = self.env['stock.picking.type'].search([])
            if rec.move_type == 'out_invoice':
                rec.picking_type_id = picking_types.filtered(lambda p: p.code == 'outgoing')[:1]
            elif rec.move_type == 'in_invoice':
                rec.picking_type_id = picking_types.filtered(lambda p: p.code == 'incoming')[:1]

    def action_stock_move(self):
        """Function to create transfer from invoice"""
        for order in self:
            if not order.picking_type_id:
                raise UserError(_("Please select a picking type"))
            if not order.invoice_picking_id:
                pick_vals = {
                    'picking_type_id': order.picking_type_id.id,
                    'partner_id': order.partner_id.id,
                    'origin': order.name,
                    'move_type': 'direct',
                }
                if order.picking_type_id.code == 'outgoing':
                    pick_vals.update({
                        'location_dest_id': order.partner_id.property_stock_customer.id,
                        'location_id': order.picking_type_id.default_location_src_id.id,
                    })
                elif order.picking_type_id.code == 'incoming':
                    pick_vals.update({
                        'location_dest_id': order.picking_type_id.default_location_dest_id.id,
                        'location_id': order.partner_id.property_stock_supplier.id,
                    })
                picking = self.env['stock.picking'].create(pick_vals)
                order.invoice_picking_id = picking.id
                order.picking_count = 1
                stock_moves = order.invoice_line_ids.filtered(lambda line: line.product_id.type in ['product', 'consu'])
                if stock_moves:
                    stock_moves._create_stock_moves(picking)._action_confirm()._action_assign()

    def action_view_picking(self):
        """Function to view moves while clicking shipment smart button"""
        action = self.env.ref('stock.action_picking_tree_ready').sudo()
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
