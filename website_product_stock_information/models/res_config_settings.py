# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """To add fields for selecting location and stock type for stock details
    in website"""
    _inherit = 'res.config.settings'

    def _get_location_type_selection(self):
        return [('all', 'All'), ('specific', 'Specific')]

    def _get_stock_type_selection(self):
        return [('on_hand', 'On Hand Quantity'), ('forecast', 'Forecasted Quantity')]

    location_type = fields.Selection(selection='_get_location_type_selection',string="Location Type",
                                     help="Choose stock for a specific location"
                                          " or all locations.")
    stock_location_id = fields.Many2one('stock.location',
                                        string='Stock Location',
                                        help='Choose a specific location')
    stock_type = fields.Selection(string="Stock Type",selection='_get_stock_type_selection', help='Choose Stock type')

    def set_values(self):
        """Store website stock configuration values as product template defaults."""
        super().set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('product.template', 'location_type',
                      self.location_type)
        IrDefault.set('product.template', 'stock_location_id',
                      self.stock_location_id.id or
                      self.env.ref('stock.stock_location_stock'))
        IrDefault.set('product.template', 'stock_type',
                      self.stock_type)

    @api.model
    def get_values(self):
        """Retrieve saved website stock configuration values from settings."""
        res = super().get_values()
        IrDefaultGet = self.env['ir.default'].sudo()._get
        res.update(
            location_type=IrDefaultGet('product.template', 'location_type') or
                          'all',
            stock_location_id=IrDefaultGet('product.template',
                                           'stock_location_id') or
                              self.env.ref('stock.stock_location_stock'),
            stock_type=IrDefaultGet('product.template', 'stock_type') or
                       'on_hand')
        return res
