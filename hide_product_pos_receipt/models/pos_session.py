# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class PosSession(models.Model):
    """Inheriting the pos session"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Pos ui models to load add update the values in product.product"""
        result = super()._pos_ui_models_to_load()
        result += ['product.product']
        return result

    def _loader_params_product_product(self):
        """Load the hide_receipt fields in product.product"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('hide_receipt')
        return result

    def fields_get(self, allfields=None, attributes=None):
        """Supering the fields_get method"""
        fields = super().fields_get(allfields=allfields, attributes=attributes)
        return fields
