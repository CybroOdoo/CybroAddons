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
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherits 'account move' to show stock picking in invoice"""
    _inherit = 'account.move'

    def _get_stock_type_ids(self):
        """Fetch the move types and return to 'picking_type_id' field"""
        data = self.env['stock.picking.type'].search([])
        if self._context.get('default_move_type') == 'out_invoice':
            for line in data:
                if line.code == 'outgoing':
                    return line
        if self._context.get('default_move_type') == 'in_invoice':
            for line in data:
                if line.code == 'incoming':
                    return line

    picking_count = fields.Integer(string="Count", copy=False, help="Count of "
                                                                    "the "
                                                                    "created "
                                                                    "picking")
    invoice_picking_id = fields.Many2one(comodel_name='stock.picking',
                                         string="Picking Id", copy=False,
                                         help="corresponding picking")
    picking_type_id = fields.Many2one(comodel_name='stock.picking.type',
                                      string='Picking Type',
                                      default=_get_stock_type_ids,
                                      help="This will determine picking "
                                           "type of incoming shipment")

    def action_stock_move(self):
        """Function to create transfer from invoice"""
        if not self.picking_type_id:
            raise UserError(_(
                " Please select a picking type"))
        for order in self:
            if not self.invoice_picking_id:
                pick = {}
                if self.picking_type_id.code == 'outgoing':
                    pick = {
                        'picking_type_id': self.picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'location_dest_id': self.partner_id.
                        property_stock_customer.id,
                        'location_id': self.picking_type_id.
                        default_location_src_id.id,
                        'move_type': 'direct'
                    }
                if self.picking_type_id.code == 'incoming':
                    pick = {
                        'picking_type_id': self.picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'location_dest_id': self.picking_type_id.
                        default_location_dest_id.id,
                        'location_id': self.partner_id.
                        property_stock_supplier.id,
                        'move_type': 'direct'
                    }
                picking = self.env['stock.picking'].create(pick)
                self.invoice_picking_id = picking.id
                self.picking_count = len(picking)
                order = order.invoice_line_ids.filtered(lambda item:
                                                        item.product_id.type in
                                                        ['product', 'consu'])
                (order._create_stock_moves(picking)._action_confirm().
                 _action_assign())

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
