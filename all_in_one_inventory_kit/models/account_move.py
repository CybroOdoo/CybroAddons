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
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherits Account Move"""
    _inherit = 'account.move'

    picking_id = fields.Many2one(
        'stock.picking',
        string='Picking',
        help="picking type"
    )
    invoice_picking_id = fields.Many2one(
        'stock.picking',
        string="Stock Pickings",
        copy=False,
        help="Select a Stock picking"
    )
    picking_count = fields.Integer(
        string="Count",
        compute="_compute_picking_count",
        help="Picking Count"
    )
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Picking Type',
        default=lambda self: self._get_stock_type_ids(),
        help="This will determine picking type of incoming shipment"
    )
    transfer_created = fields.Boolean(
        string='Transfer Created'
    )

    def _get_stock_type_ids(self):
        """Gets stock types"""
        data = self.env['stock.picking.type'].search([])
        if self.env.context.get('default_move_type') == 'out_invoice':
            for line in data:
                if line.code == 'outgoing':
                    return line
        if self.env.context.get('default_move_type') == 'in_invoice':
            for line in data:
                if line.code == 'incoming':
                    return line

    @api.depends('invoice_picking_id')
    def _compute_picking_count(self):
        for move in self:
            move.picking_count = 1 if move.invoice_picking_id else 0

    def action_stock_move(self):
        """ Button action for Transfer """
        for order in self:
            if not order.picking_type_id:
                raise UserError(_("Please select a picking type"))
            if not order.invoice_picking_id:
                pick = {}
                if order.picking_type_id.code == 'outgoing':
                    dest_id = order.partner_id.property_stock_customer.id
                    src_id = order.picking_type_id.default_location_src_id.id
                    pick = {
                        'picking_type_id': order.picking_type_id.id,
                        'partner_id': order.partner_id.id,
                        'origin': order.name,
                        'location_dest_id': dest_id,
                        'location_id': src_id,
                        'move_type': 'direct',
                        'invoice_created': True
                    }
                if order.picking_type_id.code == 'incoming':
                    dest_id = order.picking_type_id.default_location_dest_id.id
                    src_id = order.partner_id.property_stock_supplier.id
                    pick = {
                        'picking_type_id': order.picking_type_id.id,
                        'partner_id': order.partner_id.id,
                        'origin': order.name,
                        'location_dest_id': dest_id,
                        'location_id': src_id,
                        'move_type': 'direct',
                        'invoice_created': True
                    }
                picking = self.env['stock.picking'].create(pick)
                order.invoice_picking_id = picking.id
                order.picking_id = picking.id
                order.invoice_origin = picking.name
                order.transfer_created = True
                valid_lines = order.invoice_line_ids.filtered(
                    lambda r: getattr(r.product_id, 'is_storable', False)
                    or r.product_id.type in ['product', 'consu']
                )
                moves = valid_lines._create_stock_moves(picking)
                move_ids = moves._action_confirm()
                move_ids._action_assign()

    def action_view_picking(self):
        """ Shows corresponding picking in smart tab """
        self.ensure_one()
        return {
            'name': _('Picking'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_picking_id.id,
            'domain': [('id', '=', self.invoice_picking_id.id)],
        }

    def _reverse_moves(self, default_values_list=None, cancel=False):
        """ Reverse a recordset of account.move.
        If cancel parameter is true, the reconcilable or liquidity lines
        of each original move will be reconciled with its reverse's.
        :param default_values_list: A list of default values to consider per
         move.('type' & 'reversed_entry_id' are computed in the method).
        :return: An account move recordset, reverse of the current self.
        """
        for move in self:
            if move.picking_type_id.code == 'outgoing':
                data = self.env['stock.picking.type'].search(
                    [('company_id', '=', move.company_id.id),
                     ('code', '=', 'incoming')], limit=1)
                move.picking_type_id = data.id
            elif move.picking_type_id.code == 'incoming':
                data = self.env['stock.picking.type'].search(
                    [('company_id', '=', move.company_id.id),
                     ('code', '=', 'outgoing')], limit=1)
                move.picking_type_id = data.id
        return super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )
