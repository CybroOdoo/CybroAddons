# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Yadhu Shankar E(<https://www.cybrosys.com>)
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
#############################################################################
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """Extend product.product POS data loading to return stock quantities
    scoped to the POS session's configured source location
    (pos.config → picking_type_id → default_location_src_id) instead of
    the company-wide total."""

    _inherit = 'product.product'

    @api.model
    def _load_pos_data_fields(self, config):
        """Add qty_available, virtual_available and type to the fields
        loaded into the POS session for each product.product record.
        In Odoo 19, `config` here is the pos.config record object."""
        fields = super()._load_pos_data_fields(config)
        for field in ('qty_available', 'virtual_available', 'type'):
            if field not in fields:
                fields.append(field)
        return fields

    @api.model
    def _load_pos_data_read(self, records, config):
        """After the base read, replace qty_available / virtual_available
        with quantities scoped to the POS source location by directly
        querying stock.quant — the most reliable approach.
        """
        _logger.info("pos_restrict_product_stock: _load_pos_data_read CALLED, config=%s", config)

        result = super()._load_pos_data_read(records, config)

        # Get the source location from the POS operation type
        location = config.picking_type_id.default_location_src_id
        _logger.info(
            "pos_restrict_product_stock: config='%s' | picking_type='%s' (id=%s) | "
            "location='%s' (id=%s) | location.complete_name='%s' | "
            "location.location_id='%s'",
            config.name,
            config.picking_type_id.display_name, config.picking_type_id.id,
            location.display_name, location.id,
            location.complete_name,
            location.location_id.complete_name,
        )
        if not location:
            _logger.warning(
                "pos_restrict_product_stock: No source location on "
                "picking_type_id '%s' for POS config '%s'. "
                "Falling back to global stock.",
                config.picking_type_id.display_name, config.name,
            )
            return result

        _logger.info(
            "pos_restrict_product_stock: Filtering stock to location '%s' "
            "(id=%s) for POS config '%s'",
            location.display_name, location.id, config.name
        )

        product_ids = [d['id'] for d in result if d.get('id')]

        # Direct quant query: sum on-hand quantities at the source location
        # and all its children (child_of handles the sub-location hierarchy).
        quant_data = list(self.env['stock.quant']._read_group(
            [
                ('location_id', 'child_of', location.id),
                ('product_id', 'in', product_ids),
            ],
            groupby=['product_id'],
            aggregates=['quantity:sum', 'reserved_quantity:sum'],
        ))

        _logger.info(
            "pos_restrict_product_stock: quant_data raw for location %s (id=%s): %s",
            location.display_name, location.id,
            [(p.id, p.display_name, oh, res) for p, oh, res in quant_data]
        )

        # Build lookup: product_id → (on_hand, reserved)
        qty_map = {}
        virtual_map = {}
        for product, on_hand, reserved in quant_data:
            pid = product.id
            qty_map[pid] = on_hand or 0.0
            virtual_map[pid] = (on_hand or 0.0) - (reserved or 0.0)

        _logger.info(
            "pos_restrict_product_stock: qty_map for location %s: %s",
            location.display_name, qty_map
        )

        # Overwrite the global values in each product dict
        for product_dict in result:
            pid = product_dict.get('id')
            # Always set — if not in map, product has 0 at this location
            product_dict['qty_available'] = qty_map.get(pid, 0.0)
            product_dict['virtual_available'] = virtual_map.get(pid, 0.0)

        return result
