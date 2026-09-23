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
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Include qty_available and virtual_available in the template fields
        sent to the POS session. Location-scoped values are injected by the
        _load_pos_data_read override below."""
        fields = super(ProductTemplate, self)._load_pos_data_fields(config_id)
        if 'qty_available' not in fields:
            fields.append('qty_available')
        if 'virtual_available' not in fields:
            fields.append('virtual_available')
        return fields

    @api.model
    def _load_pos_data_read(self, records, config):
        """After the base read, replace qty_available / virtual_available
        with quantities scoped to the POS source location by directly
        querying stock.quant.
        """
        result = super()._load_pos_data_read(records, config)

        # Get the source location from the POS operation type
        picking_type = getattr(config, 'picking_type_id', False)
        location = picking_type.default_location_src_id if picking_type else False
        if not location:
            _logger.warning(
                "pos_restrict_product_stock: No source location on "
                "picking_type_id '%s' for POS config '%s'. "
                "Falling back to global stock.",
                picking_type.display_name if picking_type else 'N/A', getattr(config, 'name', 'N/A'),
            )
            return result

        _logger.info(
            "pos_restrict_product_stock: Filtering product.template stock to location '%s' "
            "(id=%s) for POS config '%s'",
            location.display_name, location.id, config.name
        )

        template_ids = [d['id'] for d in result if d.get('id')]

        # Direct quant query: sum on-hand quantities at the source location
        # and all its children (child_of handles the sub-location hierarchy).
        quant_data = list(self.env['stock.quant']._read_group(
            [
                ('location_id', 'child_of', location.id),
                ('product_tmpl_id', 'in', template_ids),
            ],
            groupby=['product_tmpl_id'],
            aggregates=['quantity:sum', 'reserved_quantity:sum'],
        ))

        _logger.info(
            "pos_restrict_product_stock: product.template quant_data raw for location %s (id=%s): %s",
            location.display_name, location.id,
            [(pt.id, pt.display_name, oh, res) for pt, oh, res in quant_data]
        )

        # Build lookup: product_tmpl_id → (on_hand, reserved)
        qty_map = {}
        virtual_map = {}
        for tmpl, on_hand, reserved in quant_data:
            tid = tmpl.id
            qty_map[tid] = on_hand or 0.0
            virtual_map[tid] = (on_hand or 0.0) - (reserved or 0.0)

        _logger.info(
            "pos_restrict_product_stock: product.template qty_map for location %s: %s",
            location.display_name, qty_map
        )

        # Overwrite the global values in each template dict
        for tmpl_dict in result:
            tid = tmpl_dict.get('id')
            # Always set — if not in map, product template has 0 at this location
            tmpl_dict['qty_available'] = qty_map.get(tid, 0.0)
            tmpl_dict['virtual_available'] = virtual_map.get(tid, 0.0)

        return result
