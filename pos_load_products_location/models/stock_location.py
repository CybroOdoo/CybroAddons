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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
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
        Retrieve products based on the stock location specified in the POS
        settings.
        """
        source_loc_id = self.env['ir.config_parameter'].sudo().get_param(
            'pos_load_products_location.source_loc_id')
        if not source_loc_id:
            return []
        try:
            location = self.env['stock.location'].browse(int(source_loc_id))
            if not location.exists():
                return []
            products = location.quant_ids.filtered(lambda q: q.quantity > 0).mapped('product_id')
            return products.ids
        except (ValueError, TypeError):
            return []
