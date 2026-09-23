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
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """inherit product.template to add field."""
    _inherit = ["product.template"]

    deny = fields.Integer(string="Deny POS Order", default=0,
                          help="Set a limit so that you can deny POS Order")

    @api.model
    def _load_pos_data_fields(self, config):
        """Returns the fields to be loaded for POS data."""
        result = super()._load_pos_data_fields(config)
        result.extend(['qty_available', 'incoming_qty', 'outgoing_qty', 'deny'])
        return result

    @api.model
    def _load_pos_data_read(self, records, config):
        """Pass stock location context if filtering by current warehouse."""
        if config and config.location_from == 'current_warehouse' and config.pos_stock_location_id:
            records = records.with_context(location=config.pos_stock_location_id.id)
        return super()._load_pos_data_read(records, config)


class ProductProduct(models.Model):
    """inherit product.product to load field in pos."""
    _inherit = ['product.product', 'pos.load.mixin']

    @api.model
    def _load_pos_data_fields(self, config):
        """Returns the fields to be loaded for POS data."""
        result = super()._load_pos_data_fields(config)
        result.extend(['qty_available', 'incoming_qty', 'outgoing_qty', 'deny'])
        return result

    @api.model
    def _load_pos_data_read(self, records, config):
        """Pass stock location context if filtering by current warehouse."""
        if config and config.location_from == 'current_warehouse' and config.pos_stock_location_id:
            records = records.with_context(location=config.pos_stock_location_id.id)
        return super()._load_pos_data_read(records, config)
