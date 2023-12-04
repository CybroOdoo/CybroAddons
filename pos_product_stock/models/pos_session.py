# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
from odoo import api, models


class PosSession(models.Model):
    """inherit pos. session to add fields and modules in session."""
    _inherit = 'pos.session'

    @api.model
    def _pos_ui_models_to_load(self):
        """ we use super function inorder to extend the _pos_ui_models
        _to_load function and added  res.config.settings ,
        stock.quant,stock.move.line"""
        result = super()._pos_ui_models_to_load()
        result += [
            'res.config.settings',
            'stock.quant',
            'stock.move.line',
        ]
        return result

    def _loader_params_product_product(self):
        """to load  product. product in session"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('qty_available')
        result['search_params']['fields'].append('incoming_qty')
        result['search_params']['fields'].append('outgoing_qty')
        result['search_params']['fields'].append('free_qty')
        result['search_params']['fields'].append('deny')
        result['search_params']['fields'].append('detailed_type')
        return result

    def _loader_params_stock_quant(self):
        """load  some fields with certain domain of stock.quant in session"""
        location_id = self.config_id.pos_stock_location_id
        return {
            'search_params': {
                'domain': ['|', ('location_id', '=', location_id.id),
                           ('location_id', 'in', location_id.child_ids.ids)],
                'fields': ['product_id', 'available_quantity', ''
                                                               'quantity', 'location_id'],
            },
        }

    def _loader_params_stock_move_line(self):
        """load some fields of stock.move.line in session"""
        return {
            'search_params': {
                'fields': ['product_id', 'location_dest_id', 'qty_done', 'location_id'],
            },
        }

    def _loader_params_res_config_settings(self):
        """load  some fields of base settings in session"""
        return {
            'search_params': {
                'fields': ['display_stock', 'stock_type',
                           'stock_from', 'stock_location_id'],
            }
        }

    def _get_pos_ui_res_config_settings(self, params):
        """this function should use the search_read
        method to search and read records from the base setting"""
        config_settings = self.env['res.config.settings'].search_read(**params['search_params'])
        if config_settings:
            last_config_setting = config_settings[-1]
            return last_config_setting
        else:
            last_config_setting = False
            return last_config_setting

    def _get_pos_ui_stock_quant(self, params):
        """this function should use the search_read method
        to search and read records from the  stock.quant"""
        return self.env['stock.quant']. \
            search_read(**params['search_params'])

    def _get_pos_ui_stock_move_line(self, params):
        """this function should use the search_read'method to
        search and read records from the stock.move.line'"""
        return self.env['stock.move.line'] \
            .search_read(**params['search_params'])
