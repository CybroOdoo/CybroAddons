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
from odoo import api, Command, fields, models


class PurchaseOrderLine(models.Model):
    """
    Inherits Purchase Order Line to add extra fields and functionalities
    related to the automatic stock lot creation.
    """
    _inherit = "purchase.order.line"

    _rec_names_search = ['order_id.name', 'product_id.name', 'name']

    lot_id = fields.Many2one(
        'custom.stock.lot', string='Lot', copy=False,
        help="Lot name to create for this order line")
    is_lot_product = fields.Boolean(
        string="Lot Product", compute="_compute_is_lot_product",
        search="_search_is_lot_product")

    @api.depends('product_id', 'product_id.tracking')
    def _compute_is_lot_product(self):
        for line in self:
            line.is_lot_product = bool(
                line.product_id
                and line.product_id.tracking in ('lot', 'serial')
            )

    def _search_is_lot_product(self, operator, value):
        is_pos = (
            (operator in ('=', '==') and value)
            or (operator in ('!=', '<>') and not value)
        )
        if is_pos:
            return [('product_id.tracking', 'in', ('lot', 'serial'))]
        return [
            '|',
            ('product_id', '=', False),
            ('product_id.tracking', 'not in', ('lot', 'serial')),
        ]

    def _get_auto_lot_name(self):
        """Generate a default lot name based on PO reference and product."""
        self.ensure_one()
        order_ref = self.order_id.name or 'PO'
        code = self.product_id.default_code or self.product_id.name or 'ITEM'
        code = ''.join(c for c in code if c.isalnum() or c in ('-', '_'))[:12]
        base_name = f"{order_ref}-{code}"
        other_lines = (self.order_id.order_line - self).filtered(
            lambda other_line: other_line.lot_id and other_line.lot_id.name
        )
        existing_names = {other_line.lot_id.name for other_line in other_lines}
        if base_name not in existing_names:
            return base_name
        idx = 1
        while f"{base_name}-{idx}" in existing_names:
            idx += 1
        return f"{base_name}-{idx}"

    def _ensure_custom_stock_lot(self):
        """Ensure custom stock lot exists and inverse line_id is set."""
        for line in self:
            if line.is_lot_product:
                if not line.lot_id:
                    lot_name = line._get_auto_lot_name()
                    line.lot_id = self.env['custom.stock.lot'].create({
                        'name': lot_name,
                        'line_id': line.id,
                    })
                elif line.lot_id.line_id != line:
                    line.lot_id.line_id = line.id

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.lot_id and line.lot_id.line_id != line:
                line.lot_id.line_id = line.id
        return lines

    def write(self, vals):
        res = super().write(vals)
        if 'lot_id' in vals:
            for line in self:
                if line.lot_id and line.lot_id.line_id != line:
                    line.lot_id.line_id = line.id
        return res

    def _prepare_stock_moves(self, picking=False):
        res = super()._prepare_stock_moves(picking)
        for line in self:
            if not (
                line.is_lot_product
                and line.product_id.tracking in ('lot', 'serial')
            ):
                continue
            line._ensure_custom_stock_lot()
            base_lot_name = line.lot_id.name or line._get_auto_lot_name()
            is_serial = line.product_id.tracking == 'serial'

            for val in res:
                move_qty = val.get('product_uom_qty', 0.0)
                if move_qty <= 0:
                    continue
                move_uom_id = val.get('uom_id')
                move_uom = (
                    self.env['uom.uom'].browse(move_uom_id)
                    if move_uom_id else line.uom_id
                )
                loc_id = val.get('location_id')
                loc_dest_id = val.get('location_dest_id')
                move_lines = []

                if is_serial:
                    qty_in_prod_uom = move_uom._compute_quantity(
                        move_qty, line.product_id.uom_id
                    )
                    num_serials = int(round(qty_in_prod_uom))
                    for i in range(num_serials):
                        serial_name = (
                            f"{base_lot_name}-{i + 1:03d}"
                            if num_serials > 1 else base_lot_name
                        )
                        line_vals = {
                            'product_id': line.product_id.id,
                            'lot_name': serial_name,
                            'quantity': 1.0,
                            'uom_id': line.product_id.uom_id.id,
                        }
                        if loc_id:
                            line_vals['location_id'] = loc_id
                        if loc_dest_id:
                            line_vals['location_dest_id'] = loc_dest_id
                        move_lines.append(Command.create(line_vals))
                else:
                    line_vals = {
                        'product_id': line.product_id.id,
                        'lot_name': base_lot_name,
                        'quantity': move_qty,
                    }
                    if move_uom_id:
                        line_vals['uom_id'] = move_uom_id
                    if loc_id:
                        line_vals['location_id'] = loc_id
                    if loc_dest_id:
                        line_vals['location_dest_id'] = loc_dest_id
                    move_lines.append(Command.create(line_vals))

                if move_lines:
                    val.setdefault('move_line_ids', []).extend(move_lines)
        return res
