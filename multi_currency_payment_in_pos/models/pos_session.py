# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo import models


class PosSession(models.Model):
    """Inherited this model and  added customize loader parameters for
    retrieving currency-related data,Retrieve currency information for
    the POS session's user interface."""
    _inherit = 'pos.session'

    def _loader_params_res_currency(self):
        """Customize loader parameters for retrieving currency-related data."""
        result = super()._loader_params_res_currency()
        result['params'] = {
            'search_params': {
                'domain': [],
                'fields': [],
            },
        }
        return result

    def _get_pos_ui_res_currency(self, params):
        """Retrieve currency information for the POS session's user interface.
        """
        result = super()._get_pos_ui_res_currency(params)
        currencies = self.config_id.currency_ids
        currency_params = self.env['res.currency'].search_read([('id', 'in', currencies.ids)])
        result['currency_params'] = currency_params
        return result
