# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
"""This module enables users to place online orders and
pick up their purchases from nearby stores. """
from odoo import fields, models


class PosConfig(models.Model):
    """inherited for adding address in pos session"""
    _inherit = 'pos.config'

    street = fields.Char('Street', required=True,
                         help='Enter Address for your store')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', help='Enter zip for your store')
    city = fields.Char('City', required=True,
                       help='Enter your store located city')
    state_id = fields.Many2one("res.country.state", string='State',
                               required=True, help='Enter state')
    country_id = fields.Many2one('res.country', string='Country', required=True)


class InheritPosSession(models.Model):
    """inherit pos session for load models in pos"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """load Meals Planning and Menu.Meals model in pos."""
        result = super()._pos_ui_models_to_load()
        result.extend(['stock.picking', 'stock.move'])
        return result

    def _loader_params_stock_picking(self):
        """ returning corresponding data to pos"""
        data = []
        stock_picking = self.env['stock.picking'].search([
            ('state', '!=', ['done', 'cancelled'])])
        for rec in stock_picking:
            data.append(rec.id)
        return {
            'search_params': {
                'domain': [('id', '=', data)],
                'fields': ['state', 'origin', 'move_ids_without_package']
            }
        }

    def _loader_params_stock_move(self):
        """load stock.move model in pos"""
        return {
            'search_params': {
                'fields': ['product_id', 'sale_line_id', 'picking_id']
            }
        }

    def _get_pos_ui_stock_picking(self, params):
        """get params in stock picking"""
        return self.env['stock.picking'].search_read(
            **params['search_params'])

    def _get_pos_ui_stock_move(self, params):
        """get params in stock move"""
        return self.env['stock.move'].search_read(
            **params['search_params'])
