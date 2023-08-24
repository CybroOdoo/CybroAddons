# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
    This class inherits the pos.session model and adds custom functionality
     related to POS UI models and res.users.
    """

    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """
        Returns a list of models to load for the POS UI with 'res.users'
         added to the list.
        """
        result = super()._pos_ui_models_to_load()
        result.append('res.users')
        return result

    def _loader_params_res_users(self):
        """
        Returns a dictionary of loader parameters for the 'res.users' model.
        """
        return {
            'search_params': {
                'fields': ['name'],
            },
        }

    def _get_pos_ui_res_users(self, params):
        """
        Returns a list of dictionaries containing the names of all users in the
         'res.users' model.
        """
        return self.env['res.users'].search_read(**params['search_params'])
