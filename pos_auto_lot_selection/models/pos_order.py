# -*- coding: utf-8 -*-
from odoo import api, models

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _process_order(self, order, draft, existing_order):
        """
        Ensure lots are properly updated after POS order validation.
        """
        # Call the original method
        pos_order_id = super(PosOrder, self)._process_order(order, draft, existing_order)

        # Make sure we have the record, not just an ID
        pos_order = pos_order_id
        if isinstance(pos_order_id, int):
            pos_order = self.browse(pos_order_id)

        # Now safely loop through order lines
        for order_line in pos_order.lines:
            if order_line.pack_lot_ids:
                self._update_lot_stock(order_line)

        return pos_order_id

    def _update_lot_stock(self, order_line):
        """Deduct quantities from the correct lots when POS order is validated"""
        product = order_line.product_id
        pos_config = order_line.order_id.session_id.config_id
        location_id = pos_config.picking_type_id.default_location_src_id.id

        for pack_lot in order_line.pack_lot_ids:
            lot = self.env['stock.lot'].search([
                ('name', '=', pack_lot.lot_name),
                ('product_id', '=', product.id)
            ], limit=1)

            if not lot:
                continue

            # Get all quants for this lot at POS location
            quants = self.env['stock.quant'].sudo().search([
                ('product_id', '=', product.id),
                ('lot_id', '=', lot.id),
                ('location_id', '=', location_id)
            ])
            if not quants:
                continue

            qty_to_deduct = abs(order_line.qty)  # ensure positive qty

            for quant in quants:
                if qty_to_deduct <= 0:
                    break

                if quant.quantity >= qty_to_deduct:
                    quant.quantity -= qty_to_deduct
                    qty_to_deduct = 0
                else:
                    qty_to_deduct -= quant.quantity
                    quant.quantity = 0

            # Optional: mark as taken if fully used
            remaining_qty = sum(quants.mapped('quantity'))
            lot.is_taken = remaining_qty <= 0
