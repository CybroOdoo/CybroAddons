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
        fields = super()._load_pos_data_fields(config_id)
        for field in ('qty_available', 'virtual_available', 'is_storable'):
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

        template_ids = [d['id'] for d in result if d.get('id')]
        templates = self.browse(template_ids).with_context(
            location=location.id
        )
        qty_map = {
            t.id: (t.qty_available, t.virtual_available)
            for t in templates
        }

        # Overwrite the quantities in each template dict
        for tmpl_dict in result:
            tid = tmpl_dict.get('id')
            if tid in qty_map:
                on_hand, virtual = qty_map[tid]
                tmpl_dict['qty_available'] = on_hand
                tmpl_dict['virtual_available'] = virtual
            else:
                tmpl_dict['qty_available'] = 0.0
                tmpl_dict['virtual_available'] = 0.0

        return result
