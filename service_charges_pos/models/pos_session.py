# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
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
################################################################################
from odoo import models


class PosSession(models.Model):
    ''' Inherit pos.session to add service product to the product list'''
    _inherit = 'pos.session'

    def _get_pos_ui_product_product(self, params):
        """Add service product to the product list if service charges is"""
        result = super()._get_pos_ui_product_product(params)
        service_product_id = self.config_id.service_product_id.id
        product_ids_set = {product['id'] for product in result}

        if self.config_id.is_service_charges and (
                service_product_id) not in product_ids_set:
            product_model = self.env['product.product'].with_context(
                **params['context'])
            product = product_model.search_read([(
                'id', '=', service_product_id
            )], fields=params['search_params']['fields'])
            self._process_pos_ui_product_product(product)
            result.extend(product)
        return result
