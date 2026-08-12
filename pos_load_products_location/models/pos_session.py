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
from odoo import models


class PoSSession(models.Model):
    """
        Inherits the pos.session model to customize product
        loading behavior in the POS UI.
    """
    _inherit = "pos.session"

    def _get_pos_ui_product_product(self, params):
        """
        Legacy helper kept for compatibility if called during UI loading.
        """
        context = params.get('context', {}) if isinstance(params, dict) else {}
        search_params = params.get('search_params', {}) if isinstance(params, dict) else {}
        self = self.with_context(**context)
        if not self.config_id.limited_products_loading:
            products = self.env['product.product'].search_read(**search_params)
        else:
            fields = search_params.get('fields', [])
            products = self.config_id.get_limited_products_loading(fields)
        if hasattr(self, '_process_pos_ui_product_product'):
            self._process_pos_ui_product_product(products)
        default_src_loc = self.config_id.picking_type_id.default_location_src_id
        if default_src_loc:
            products_in_src = default_src_loc.quant_ids.filtered(
                lambda l: l.quantity > 0).mapped('product_id')
            return [rec for rec in products if rec['id'] in products_in_src.ids]
        return products
