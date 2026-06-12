# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from collections import Counter

from odoo import api, fields, models
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class ProductionLot(models.Model):
    _inherit = "stock.lot"

    is_taken = fields.Boolean(
        string='Taken lot',
        default=False,
        help='If enabled, this lot number is taken'
    )

    @api.model
    def get_available_lots_for_pos(self, product_id, quantity=1, fetched_assigned_lots=None):
        """
        Get available lots for a product suitable for the Point of Sale (PoS).
        Retrieves available lots based on the configured removal strategy
        (FIFO, LIFO, FEFO), filtered by actual on-hand stock in quants.
        """
        if fetched_assigned_lots is None:
            fetched_assigned_lots = []

        company_id = self.env.company.id

        product = self.env['product.product'].browse(product_id)
        if not product.exists():
            return False

        removal_strategy = (
            product.categ_id.removal_strategy_id.method
            if product.categ_id.removal_strategy_id
            else 'fifo'
        )

        # --- Resolve POS stock location ---
        pos_config = self.env['pos.config'].sudo().search(
            [('company_id', '=', company_id)], limit=1
        )
        stock_location_id = (
            pos_config.picking_type_id.default_location_src_id.id
            if pos_config and pos_config.picking_type_id.default_location_src_id
            else None
        )

        # --- Build quant domain for actual available stock ---
        quant_domain = [
            ('product_id', '=', product_id),
            ('quantity', '>', 0),
            ('lot_id', '!=', False),
            ('lot_id.is_taken', '=', False),
            '|',
            ('company_id', '=', company_id),
            ('company_id', '=', False),
        ]
        if stock_location_id:
            quant_domain.append(('location_id', 'child_of', stock_location_id))

        # Ordering is handled in Python below (.sorted()) because ORM ordering
        # on related fields (lot_id.*) is unreliable; fetch all matching quants.
        quants = self.env['stock.quant'].sudo().search(quant_domain)

        # --- Sort in Python for LIFO/FEFO since ORM ordering on related fields is limited ---
        try:
            now_dt = fields.Datetime.now()
            if removal_strategy == 'fefo':
                quants = quants.sorted(
                    key=lambda q: (
                        getattr(q.lot_id, 'removal_date', False) or getattr(q.lot_id, 'expiration_date', False) or getattr(q.lot_id, 'use_date', False) or now_dt,
                        getattr(q, 'in_date', False) or q.lot_id.create_date or now_dt,
                        q.id
                    )
                )
            elif removal_strategy == 'lifo':
                quants = quants.sorted(
                    key=lambda q: (getattr(q, 'in_date', False) or q.lot_id.create_date or now_dt, q.id),
                    reverse=True
                )
            else:  # fifo
                quants = quants.sorted(
                    key=lambda q: (getattr(q, 'in_date', False) or q.lot_id.create_date or now_dt, q.id)
                )
        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                "pos_auto_lot_selection: lot sorting failed for product %s "
                "(strategy=%s), falling back to ORM order. Error: %s",
                product_id, removal_strategy, exc
            )

        # --- Count occurrences of each lot name already assigned in POS ---
        assigned_lot_counts = Counter(fetched_assigned_lots)

        # --- Select lots to fulfill requested quantity ---
        selected_lot_names = []
        remaining_qty = float(quantity)
        precision = product.uom_id.rounding  # correct field

        for quant in quants:
            if float_compare(remaining_qty, 0, precision_rounding=precision) <= 0:
                break

            lot = quant.lot_id
            available_qty = quant.quantity - quant.reserved_quantity

            # Deduct quantities already assigned in the current POS session
            assigned_qty = assigned_lot_counts.get(lot.name, 0)
            if assigned_qty > 0:
                deduct_qty = min(available_qty, assigned_qty)
                available_qty -= deduct_qty
                assigned_lot_counts[lot.name] -= deduct_qty

            if float_compare(available_qty, 0, precision_rounding=precision) <= 0:
                continue

            taken = min(remaining_qty, available_qty)
            count = int(taken)

            if count > 0:
                selected_lot_names.extend([lot.name] * count)
                remaining_qty -= count

        return selected_lot_names if selected_lot_names else False