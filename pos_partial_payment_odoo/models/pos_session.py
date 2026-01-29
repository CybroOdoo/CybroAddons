# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj(odoo@cybrosys.info)
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
    """
    This class extends the 'pos.session' model to add functionality related to loading
    parameters of the 'res.partner' model within the session
    """
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """
        Returns a list of models to load for the POS UI with 'res.users'
         added to the list.
        """
        result = super()._pos_ui_models_to_load()
        result.append('res.partner')
        return result

    def _loader_params_res_partner(self):
        """Load res.config.settings parameters"""
        return {
            'search_params': {
                'fields': ['prevent_partial_payment']
            }
        }

    def _get_pos_ui_res_partner(self, params):
        """
        Returns a list of dictionaries containing the names of all users in the
         'res.users' model.
        """
        return self.env['res.partner'].search_read(**params['search_params'])
