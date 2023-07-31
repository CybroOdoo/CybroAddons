# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
from ast import literal_eval
from odoo import models


class PosSession(models.Model):
    """Inherited model for extending the Point of Sale sessions."""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Add 'pos.custom.message' to the models to be loaded in the Point of
        Sale UI."""
        res = super()._pos_ui_models_to_load()
        res.append('pos.custom.message')
        return res

    def _loader_params_pos_custom_message(self):
        """Retrieve the loader parameters for 'pos.custom.message'."""
        ids = (self.env['ir.config_parameter'].sudo().get_param(
            'pos_custom_message.message_ids'))
        if ids:
            message_ids = self.browse(literal_eval(ids))
            domain = [('id', 'in', message_ids.ids)]
        else:
            domain = ""
        return {
            'search_params': {
                'domain': domain,
                'fields': [
                    'message_type', 'title', 'message_text', 'execution_time',
                    'pos_config_ids'
                ],
            }
        }

    def _get_pos_ui_pos_custom_message(self, params):
        """Get 'pos.custom.message' records based on the provided search
        parameters."""
        return self.env['pos.custom.message'].search_read(
            **params['search_params'])
