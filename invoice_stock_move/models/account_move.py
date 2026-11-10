# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Extend account.move to create stock pickings from an invoice."""
    _inherit = 'account.move'

    picking_count = fields.Integer(
        string="Count", copy=False, help="Count of the created pickings.")
    invoice_picking_id = fields.Many2one(
        comodel_name='stock.picking', string="Picking Id", copy=False,
        help="Picking created from this invoice.")
    picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        compute='_compute_picking_type_id',
        help="Determines the picking type of the incoming or outgoing "
             "shipment.")

    @api.depends('move_type', 'company_id')
    def _compute_picking_type_id(self):
        """Compute the picking type from the invoice type and the company."""
        picking_types = {}
        for move in self:
            move_type = (self.env.context.get('default_move_type')
                         or move.move_type)
            if move_type in ('out_invoice', 'out_refund'):
                code = 'outgoing'
            elif move_type in ('in_invoice', 'in_refund'):
                code = 'incoming'
            else:
                move.picking_type_id = False
                continue
            company = move.company_id or self.env.company
            key = (code, company.id)
            if key not in picking_types:
                picking_types[key] = self.env['stock.picking.type'].search(
                    [('code', '=', code), ('company_id', '=', company.id)],
                    limit=1)
            move.picking_type_id = picking_types[key]

    def _prepare_picking_vals(self):
        """Prepare the values used to create the picking of the invoice.

        :return: values for the creation of a ``stock.picking``
        :rtype: dict
        """
        self.ensure_one()
        picking_type = self.picking_type_id
        if picking_type.code == 'outgoing':
            location = picking_type.default_location_src_id
            location_dest = (
                self.partner_id.property_stock_customer
                or self.env.ref('stock.stock_location_customers'))
        else:
            location = (
                self.partner_id.property_stock_supplier
                or self.env.ref('stock.stock_location_suppliers'))
            location_dest = picking_type.default_location_dest_id
        return {
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
            'move_type': 'direct',
        }

    def action_stock_move(self):
        """Create the transfer from the invoice."""
        for move in self:
            if not move.picking_type_id:
                raise UserError(self.env._("Please select a picking type."))
            if move.invoice_picking_id:
                continue
            picking = self.env['stock.picking'].create(
                move._prepare_picking_vals())
            move.write({
                'invoice_picking_id': picking.id,
                'picking_count': 1,
            })
            lines = move.invoice_line_ids.filtered(
                lambda line: line.product_id.type == 'consu')
            stock_moves = lines._create_stock_moves(picking)
            stock_moves = stock_moves._action_confirm()
            stock_moves._action_assign()

    def action_view_picking(self):
        """Open the picking created from the invoice.

        :return: the window action showing the picking
        :rtype: dict
        """
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'stock.action_picking_tree_ready')
        action.pop('id', None)
        action['context'] = {}
        action['domain'] = [('id', '=', self.invoice_picking_id.id)]
        if self.invoice_picking_id:
            form_view = self.env.ref(
                'stock.view_picking_form', raise_if_not_found=False)
            action['views'] = [(form_view.id if form_view else False, 'form')]
            action['res_id'] = self.invoice_picking_id.id
        return action
