# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil Ashok(<https://www.cybrosys.com>)
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
    """Model Inherits to add Load models and fields"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """
        Overrides the _pos_ui_models_to_load method to include additional models
        required for the POS UI.
        :return: A list of models to load for the POS UI.
        :rtype: list[str]
        """
        result = super()._pos_ui_models_to_load()
        result.append('variants.tree')
        result.append('product.attribute.value')
        return result

    def _loader_params_variants_tree(self):
        """
        Returns the loader parameters for the 'variants.tree' model.

        :return: The loader parameters.
        :rtype: dict
        """
        return {
            'search_params': {
                'fields': ["value_ids", "attribute_id", "variants_id",
                           "extra_price"],
            },
        }

    def _loader_params_product_attribute_value(self):
        """
        Returns the loader parameters for the 'product.attribute.value' model.

        :return: The loader parameters.
        :rtype: dict
        """
        return {
            'search_params': {
                'fields': ["id", "name"],
            },
        }

    def _get_pos_ui_variants_tree(self, params):
        """
        Fetches and returns the records from the 'variants.tree'
        model based on the specified search parameters.

        :param params: The parameters for the search operation.
        :type params: dict
        :return: The fetched records.
        :rtype: list
        """
        return self.env['variants.tree'].search_read(**params['search_params'])

    def _get_pos_ui_product_attribute_value(self, params):
        """
        Fetches and returns the records from the 'product.attribute.value'
        model based on the specified search parameters.

        :param params: The parameters for the search operation.
        :type params: dict
        :return: The fetched records.
        :rtype: list
        """
        return self.env['product.attribute.value'].search_read(
            **params['search_params'])

    def _loader_params_product_product(self):
        """
        Returns the parameters for loading the 'product.product' model.

        Extends the base method to include additional fields 'pos_variants' and
        'variant_line_ids' in the search parameters.

        :return: The loader parameters.
        :rtype: dict
        """
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(
            ['is_pos_variants', 'variant_line_ids'])
        return result
