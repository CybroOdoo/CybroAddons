# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu KP (odoo@cybrosys.com)
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


class InheritPosSession(models.Model):
    """Inherit pos session for load models in pos"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Load Meals Planning and Menu.Meals model in pos."""
        result = super()._pos_ui_models_to_load()
        new_model = 'meals.planning'
        if new_model not in result:
            result.append(new_model)
        return result

    def _loader_params_meals_planning(self):
        """Returning corresponding data to pos"""
        plans = self.env['meals.planning'].search([
            ('state', '=', 'activated'),
            ('pos_ids', 'in', self.id)])
        data = plans.mapped('id')
        return {
            'search_params': {
                'domain': [('id', '=', data)],
                'fields': ['name', 'menu_product_ids', 'time_from', 'time_to',
                           'state', 'pos_ids']}}

    def _loader_params_product_product(self):
        """Load product.product parameters"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(['name', 'id'])
        return result

    def _get_pos_ui_meals_planning(self, params):
        return self.env['meals.planning'].search_read(**params['search_params'])
