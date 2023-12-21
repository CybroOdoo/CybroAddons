# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models


class PosSession(models.Model):
    """inherit the model pos.session to add the model res.lang"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """load models"""
        result = super()._pos_ui_models_to_load()
        new_model = 'res.lang'
        result.append(new_model)
        return result

    def _loader_params_res_lang(self):
        """load parameters"""
        return {
            'search_params': {
                'domain': [('active', '=', True)],
                'fields': ['name', 'code'],
            },
        }

    def _get_pos_ui_res_lang(self, params):
        """to get the languages"""
        return self.env['res.lang'].search_read(**params['search_params'])
