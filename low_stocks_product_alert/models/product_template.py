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
from odoo import api, models


class ProductTemplate(models.Model):
    """
    Inherits from 'product.template' and includes ProductLowStockAlertMixin
    to provide low stock alert tags and state.
    """
    _name = 'product.template'
    _inherit = ['product.template', 'product.low.stock.alert.mixin']

    @api.model
    def _load_pos_data_fields(self, config_id=None, **kwargs):
        """Add low stock alert fields to POS product template fields."""
        fields = super()._load_pos_data_fields(config_id, **kwargs)
        if isinstance(fields, set):
            fields.update({'alert_tag', 'alert_state'})
            return list(fields)
        for field in ('alert_tag', 'alert_state'):
            if field not in fields:
                fields.append(field)
        return fields
