# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind(<https://www.cybrosys.com>)
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
    """Inherited model POS Session for loading field in res.config.settings
        into pos session.
    Methods:
        _pos_ui_models_to_load(self):
            To load model res config settings to pos session.
        _loader_params_res_config_settings(self):
            Loads field allow_data_auto_sync to pos session.
        _get_pos_ui_res_config_settings(self, params):
            Load res config settings parameters to pos session."""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """ Load model res config settings to pos session.
            List: Returns list with model name."""
        result = super()._pos_ui_models_to_load()
        result += [
            'res.config.settings',
        ]
        return result

    def _loader_params_res_config_settings(self):
        """ Loads field allow_data_auto_sync to pos session
            dictionary: Returns dictionary of search params with fields."""
        return {
            'search_params': {
                'fields': ['allow_data_auto_sync'],
            },
        }

    def _get_pos_ui_res_config_settings(self, params):
        """ Load res config settings parameters to pos session.
            params(dict):dictionary of search param with dictionary of
                         field to load.
            list: Returns list of dictionary with search param values."""
        return self.env['res.config.settings'].search_read(
            **params['search_params'])
