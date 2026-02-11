# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, models


class PosSession(models.Model):
    """This is used to load the models and fields to pos session"""
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Override to include pos_categ_ids in product.product loader"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('pos_categ_ids')
        result['search_params']['fields'].append(
            'pos_categ_id')  # Also include computed field
        return result

    def _get_pos_ui_product_product(self, params):
        """Ensure products are filtered correctly based on restricted categories"""
        config = self.config_id

        # Check if category restriction is enabled
        if config.iface_available_categ_ids and config.iface_available_categ_ids.ids:
            # Create a domain that checks if product has at least one category
            # in the allowed categories OR has no category assigned
            domain = params['search_params'].get('domain', [])

            # Remove any existing pos_categ_id domain filters from parent
            domain = [d for d in domain if not (isinstance(d, (list, tuple)) and
                                                len(d) == 3 and
                                                d[0] == 'pos_categ_id')]

            # For multi-category support, we need to check both pos_categ_ids AND pos_categ_id
            # Products should appear if ANY of their categories are in the restricted list
            domain.extend([
                '|',  # OR condition - either condition should be true
                ('pos_categ_ids', 'in', config.iface_available_categ_ids.ids),
                # Any category in pos_categ_ids
                ('pos_categ_id', 'in', config.iface_available_categ_ids.ids),
                # OR the main category
            ])

            params['search_params']['domain'] = domain

        return super()._get_pos_ui_product_product(params)