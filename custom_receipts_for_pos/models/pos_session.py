# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sadique Kottekkat (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models


class PosSession(models.Model):
    """
       This is an Odoo model for Point of Sale (POS) sessions.
       It inherits from the 'pos.session' model and extends its functionality.

       Methods: _loader_params_product_product(): Adds the 'qty_available'
        field to the search parameters for the product loader.
    """
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Function to load the product field to the product params"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('qty_available')
        return result

    def _pos_ui_models_to_load(self):
        """Function that super the ui models loading"""
        result = super()._pos_ui_models_to_load()
        result += [
            'res.config.settings',
            'pos.receipt',
        ]
        return result

    def _loader_params_pos_receipt(self):
        """Function that returns the product field pos Receipt"""
        return {
            'search_params': {
                'fields': ['design_receipt', 'name'],

            },
        }

    def _get_pos_ui_pos_receipt(self, params):
        """Used to Return the params value to the pos Receipts"""
        return self.env['pos.receipt'].search_read(**params['search_params'])

    def _loader_params_res_config_settings(self):
        """The Function used to returns the field value"""
        return {
            'search_params': {
                'fields': ['pos_receipt_design'],

            },
        }

    def _get_pos_ui_res_config_settings(self, params):
        """Function is used to returns the config settings value"""
        return (self.env['res.config.settings'].search_read
                (**params['search_params']))
