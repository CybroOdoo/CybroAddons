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
from odoo import models, fields
from odoo.exceptions import UserError


class StockPicking(models.Model):
    """This class inherits 'stock.picking' and adds required fields """
    _inherit = 'stock.picking'

    auto_generated = fields.Boolean(
        string='Auto Generated Transfer',
        copy=False,
        help="Field helps to check whether the picking is "
             "created from another picking or not"
    )

    def button_validate(self):
        """Create counterpart inter-company transfer when picking is validated."""
        pickings_to_process = self.filtered(
            lambda p: p.state != 'done' and not p.auto_generated
        )
        res = super().button_validate()
        for picking in pickings_to_process:
            if picking.state == 'done':
                picking.create_intercompany_transfer()
        return res

    def create_intercompany_transfer(self):
        """Creating the transfer if the selected company has enabled the
        internal transfer option"""
        for picking in self:
            company_id = self.env['res.company'].sudo().search(
                [('partner_id', '=', picking.partner_id.id)], limit=1
            )
            location_id = False
            location_dest_id = False

            if company_id and company_id.enable_inter_company_transfer:
                create_transfer = False
                if (picking.picking_type_id.code ==
                        company_id.apply_transfer_type or
                        company_id.apply_transfer_type == 'all'):
                    create_transfer = True
                if create_transfer:
                    warehouse_ids = company_id.destination_warehouse_id.sudo()
                    if picking.picking_type_id.code == 'incoming':
                        operation_type_id = self.env[
                            'stock.picking.type'].sudo().search(
                            [('warehouse_id', 'in', warehouse_ids.ids),
                             ('code', '=', 'outgoing')], limit=1)
                    elif picking.picking_type_id.code == 'outgoing':
                        operation_type_id = self.env[
                            'stock.picking.type'].sudo().search(
                            [('warehouse_id', 'in', warehouse_ids.ids),
                             ('code', '=', 'incoming')], limit=1)
                    else:
                        raise UserError(
                            self.env._('Internal transfer between companies is not allowed'))
                    if operation_type_id:
                        if operation_type_id.default_location_src_id:
                            location_id = operation_type_id.default_location_src_id.id
                        elif picking.company_id.partner_id:
                            location_id = picking.company_id.partner_id.property_stock_supplier.id
                        if operation_type_id.default_location_dest_id:
                            location_dest_id = operation_type_id.default_location_dest_id.id
                        elif company_id.partner_id:
                            location_dest_id = company_id.partner_id.property_stock_customer.id
                    if location_id and location_dest_id:
                        picking_vals = {
                            'partner_id': picking.company_id.partner_id.id,
                            'company_id': company_id.id,
                            'picking_type_id': operation_type_id.id,
                            'location_id': location_id,
                            'location_dest_id': location_dest_id,
                            'auto_generated': True,
                            'origin': picking.name,
                        }
                        counterpart_picking = self.env['stock.picking'].sudo().create(
                            picking_vals)
                    else:
                        raise UserError(
                            self.env._('Please configure appropriate locations '
                                       'on Operation type/Partner'))
                    for move in picking.move_ids:
                        lines = picking.move_line_ids.filtered(
                            lambda x: x.product_id == move.product_id)
                        done_qty = sum(lines.mapped('quantity'))
                        if not done_qty:
                            done_qty = sum(lines.move_id.mapped('product_uom_qty'))
                        move_vals = {
                            'picking_id': counterpart_picking.id,
                            'picking_type_id': operation_type_id.id,
                            'product_id': move.product_id.id,
                            'uom_id': move.uom_id.id,
                            'product_uom_qty': done_qty,
                            'location_id': location_id,
                            'location_dest_id': location_dest_id,
                            'company_id': company_id.id,
                        }
                        self.env['stock.move'].sudo().create(move_vals)
                    if counterpart_picking:
                        counterpart_picking.sudo().action_confirm()
                        counterpart_picking.sudo().action_assign()
