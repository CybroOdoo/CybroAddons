"""Pos session to load the models and fields"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
from odoo import api, models


class PosSession(models.Model):
    """This is used to load the models and fields to pos session"""
    _inherit = 'pos.session'

    @api.model
    def _pos_ui_models_to_load(self):
        """This is used to load a new model to pos session"""
        result = super()._pos_ui_models_to_load()
        result += [
            'product.template',
        ]
        return result

    def _loader_params_product_template(self):
        """This is used to load the model fields"""
        return {
            'search_params': {
                'fields': ['display_name', 'default_code'],
            }
        }

    def _get_pos_ui_product_template(self, params):
        """This is used to load the model"""
        return self.env['product.template'].search_read(
            **params['search_params'])

    def _loader_params_product_product(self):
        """To load the parameter"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('alternative_product_ids')
        return result
