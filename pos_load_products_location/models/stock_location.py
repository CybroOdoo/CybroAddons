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
from odoo import models, api


class StockLocation(models.Model):
    """
    Extends stock locations with a helper to fetch products for POS loading.
    """
    _inherit = 'stock.location'

    @api.model
    def search_products_by_location(self):
        """
        Retrieve product template IDs based on the stock location specified in the POS
        settings. If no location is set, returns False indicating no restriction.
        """
        loc_id = self.env['ir.config_parameter'].sudo().get_int(
            'pos_load_products_location.source_loc_id')
        if not loc_id:
            return False

        location = self.browse(loc_id).exists()
        if not location:
            return False

        locations = self.search([('id', 'child_of', location.id)])
        quants = self.env['stock.quant'].search([
            ('location_id', 'in', locations.ids),
            ('quantity', '>', 0),
        ])
        products = quants.mapped('product_tmpl_id')
        return products.ids
