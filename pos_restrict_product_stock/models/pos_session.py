# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
from odoo import models


class PosSession(models.Model):
    """Inherited pos session for loading quantity fields from product"""
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Load forcast and on hand quantity field to pos session.
           :return dict: returns dictionary of field parameters for the
                        product model
        """
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('qty_available')
        result['search_params']['fields'].append('virtual_available')
        result['search_params']['fields'].append('detailed_type')
        # ❌ DO NOT add pos_stock_qty here (not a real field)
        return result

    def _get_pos_ui_product_product(self, params):
        """Inject warehouse-specific stock"""
        products = super()._get_pos_ui_product_product(params)
        pos_location = self.config_id.picking_type_id.default_location_src_id or \
                       self.config_id.picking_type_id.warehouse_id.lot_stock_id

        for product in products:
            product_id = product['id']
            product_record = self.env['product.product'].browse(product_id)
            product['pos_stock_qty'] = product_record.with_context(
                location=pos_location.id,
                compute_child=True
            ).qty_available
        return products
