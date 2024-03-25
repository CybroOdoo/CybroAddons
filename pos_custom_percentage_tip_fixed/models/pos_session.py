"""loads session to model"""
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
    """This class is used to inherit the pos session and loads
    the settings model"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Loading model 'pos.multi.uom' to POS"""
        result = super()._pos_ui_models_to_load()
        result.append('res.config.settings')
        return result

    def _loader_params_res_config_settings(self):
        """ This is used to load the fields"""
        return {
            'search_params': {
                'fields': ['custom_tip_percentage'],
            }
        }

    def _get_pos_ui_res_config_settings(self, params):
        """This is used to load tip to pos"""
        return self.env['res.config.settings'].search_read(**params['search_params'])
