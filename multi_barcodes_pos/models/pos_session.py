# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
#############################################################################
from odoo import models


class PosSession(models.Model):
    """
       Inherit pos session for adding multi barcode products in to session
    """
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """
            Retrieve a list of Point of Sale (POS) UI models to load,
            including the 'multi.barcode.products' model if not already
            present.
        """
        result = super()._pos_ui_models_to_load()
        new_model = 'multi.barcode.products'
        if new_model not in result:
            result.append(new_model)
        return result

    def _loader_params_multi_barcode_products(self):
        """
            Define loader parameters for the 'multi.barcode.products' model.
        """
        record = {
            'search_params': {
                'fields': ['product_multi_id', 'multi_barcode']
            }
        }
        return record

    def _loader_params_product_product(self):
        """
            Retrieve loader parameters for the 'product.product' model with
            an additional field.
        """
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('product_multi_barcodes_ids')
        return result

    def _get_pos_ui_multi_barcode_products(self, params):
        """
            Retrieve multi-barcode product records from the database based
            on the specified search parameters
        """
        record = self.env['multi.barcode.products'].search_read(
            **params['search_params'])
        return record

    def _pos_data_process(self, loaded_data):
        """
            This method is responsible for processing loaded data for
            Point of Sale (POS)
        """
        super()._pos_data_process(loaded_data)
        context = {}
        for rec in loaded_data['multi.barcode.products']:
            if rec['product_multi_id']:
                context[rec['multi_barcode']] = rec['product_multi_id'][0]
        loaded_data['multi_barcode'] = context
