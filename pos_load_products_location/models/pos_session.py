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
        Inherits the pos.session model to customize product loading behavior in the POS UI.
    """
    _inherit = "pos.session"

    def _pos_data_process(self, loaded_data):
        super()._pos_data_process(loaded_data)
        source_loc_id_str = self.env['ir.config_parameter'].sudo().get_param('pos_load_products_location.source_loc_id')
        if source_loc_id_str:
            location = self.env['stock.location'].browse(int(source_loc_id_str))
            products = location.quant_ids.filtered(lambda l: l.available_quantity > 0).mapped('product_id')
            loaded_data['product_list_by_location'] = products.ids
        else:
            loaded_data['product_list_by_location'] = [p['id'] for p in loaded_data['product.product']]

    def _get_pos_ui_product_product(self, params):
        """
        Retrieves the list of products to be displayed in the POS UI based on session settings.

        If limited product loading is enabled, it fetches a filtered set of products,
        otherwise, it retrieves all products matching the given search parameters.
        Additionally, it filters products based on their stock availability in the
        default source location of the configured picking type.

        :param dict params: Dictionary containing 'context' and 'search_params'.
        :return: List of product records to be displayed in the POS UI.
        """
        self = self.with_context(**params['context'])
        if not self.config_id.limited_products_loading:
            products = self.env['product.product'].search_read(
                **params['search_params'])
        else:
            products = self.config_id.get_limited_products_loading(
                params['search_params']['fields'])
        self._process_pos_ui_product_product(products)
        default_src_loc = self.config_id.picking_type_id.default_location_src_id
        products_in_src = default_src_loc.quant_ids.filtered(
            lambda l: l.available_quantity > 0).mapped('product_id')
        to_display = []
        for rec in products:
            if rec['id'] in products_in_src.ids:
                to_display.append(rec)
        return to_display
