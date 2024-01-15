# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP(<https://www.cybrosys.com>)
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
    """Model inherited to add additional functionality"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Used to super the _pos_ui_models_to_load"""
        result = super()._pos_ui_models_to_load()
        result += [
            'res.config.settings',
        ]
        return result

    def _loader_params_res_config_settings(self):
        """Used to override the default settings for loading fields"""
        return {
            'search_params': {
                'fields': ['customer_name',
                           'customer_address', 'customer_mobile',
                           'customer_phone', 'customer_email', 'customer_vat',
                           'customer_details'],
            },
        }

    def _get_pos_ui_res_config_settings(self, params):
        """Used to get the parameters"""
        return self.env['res.config.settings'].search_read(
            **params['search_params'])
