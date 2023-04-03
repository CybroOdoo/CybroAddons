# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu (odoo@cybrosys.com)
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
    """Inherited POS Session"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Supering the function for loading res.config.settings to pos session"""
        result = super()._pos_ui_models_to_load()
        result.append('res.config.settings')
        return result

    def _loader_params_res_config_settings(self):
        """Returning the field required"""
        return {
            'search_params': {
                'fields': ['enable_service_charge', 'visibility', 'global_selection', 'global_charge', 'global_product_id'],
            },
        }

    def _get_pos_ui_res_config_settings(self, params):
        """Returns the model"""
        return self.env['res.config.settings'].search_read(**params['search_params'])
