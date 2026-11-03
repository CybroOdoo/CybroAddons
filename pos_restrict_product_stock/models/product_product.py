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


class ProductProduct(models.Model):
    """Extend product.product POS data loading to return stock quantities
    scoped to the POS session's configured source location
    (pos.config → picking_type_id → default_location_src_id) instead of
    the company-wide total."""

    _inherit = 'product.product'

    @api.model
    def _load_pos_data_fields(self, config):
        """Add qty_available, virtual_available, type and is_storable to the
        fields loaded into the POS session for each product.product record.
        The `config` parameter is the pos.config record object."""
        fields = super()._load_pos_data_fields(config)
        for field in (
            'qty_available', 'virtual_available', 'type', 'is_storable'
        ):
            if field not in fields:
                fields.append(field)
        return fields

    @api.model
    def _load_pos_data_read(self, records, config):
        """After the base read, populate qty_available and virtual_available
        scoped to the POS source location using Odoo's location context.
        """
        result = super()._load_pos_data_read(records, config)

        # Get the source location from the POS operation type
        picking_type = getattr(config, 'picking_type_id', False)
        location = (
            picking_type.default_location_src_id if picking_type else False
        )
        if not location:
            _logger.warning(
                "pos_restrict_product_stock: No source location on "
                "picking_type_id '%s' for POS config '%s'. "
                "Falling back to global stock.",
                picking_type.display_name if picking_type else 'N/A',
                getattr(config, 'name', 'N/A'),
            )
            return result

        product_ids = [d['id'] for d in result if d.get('id')]
        products = self.browse(product_ids).with_context(
            location=location.id
        )
        qty_map = {
            p.id: (p.qty_available, p.virtual_available)
            for p in products
        }

        # Overwrite the quantities in each product dict
        for product_dict in result:
            pid = product_dict.get('id')
            if pid in qty_map:
                on_hand, virtual = qty_map[pid]
                product_dict['qty_available'] = on_hand
                product_dict['virtual_available'] = virtual
            else:
                product_dict['qty_available'] = 0.0
                product_dict['virtual_available'] = 0.0

        return result
