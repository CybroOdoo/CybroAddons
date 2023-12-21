# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class PosSessionLoadFields(models.Model):
    """Inherited model pos session for loading field in pos payment into
       pos session.
        Methods:
            _pos_ui_models_to_load(self):
                Supering the method to load model pos payment and res config
                settings into pos session
            _loader_params_res_config_settings(self):
                Loads field is_allow_payment_ref to pos session
            _get_pos_ui_res_config_settings(self, params):
                Load res config settings parameters to pos session
            _loader_params_pos_payment(self):
                Loads field user_payment_reference to pos session
            _get_pos_ui_pos_payment(self, params):
                Load pos payment parameters to pos session."""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """ Supering the method to load model pos payment and res config
            settings into pos session.
            List: Returns list with model names."""
        result = super()._pos_ui_models_to_load()
        result += [
            'pos.payment',
            'res.config.settings',
        ]
        return result

    def _loader_params_res_config_settings(self):
        """ Loads field is_allow_payment_ref to pos session.
            dictionary: Returns dictionary of search params with fields."""
        return {
            'search_params': {
                'fields': ['is_allow_payment_ref'],
            },
        }

    def _get_pos_ui_res_config_settings(self, params):
        """ Load res config settings parameters to pos session.
            params(dict):dictionary of search param with dictionary of
                         field to load.
            list: Returns list of dictionary with search param values."""
        return self.env['res.config.settings'].search_read(
            **params['search_params'])

    def _loader_params_pos_payment(self):
        """ Loads field user_payment_reference to pos session.
            dictionary: Returns dictionary of search params with fields."""
        return {'search_params': {'domain': [],
                                  'fields': ['user_payment_reference']}}

    def _get_pos_ui_pos_payment(self, params):
        """ Load pos payment parameters to pos session.
            params(dict):dictionary of search param with dictionary of
                         field to load.
            list: Returns list of dictionary with search param values."""
        return self.env['pos.payment'].search_read(**params['search_params'])
