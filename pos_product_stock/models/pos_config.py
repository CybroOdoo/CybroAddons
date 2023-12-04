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
from odoo import fields, models


class PosConfig(models.Model):
    """inherit pos.config to add fields."""
    _inherit = 'pos.config'

    pos_stock_location_id = fields.Many2one('stock.location', string='Stock Location',
                                         help="This field helps to hold the location")
    location_from = fields.Selection([('all_warehouse', 'All Location'),
                                      ('current_warehouse', 'Current Location')],
                                     string="Show Stock Of",
                                     help="can choose the location where you want to display the stock ")
    display_stock_setting = fields.Boolean(string="Display Stock",
                                           help="By enabling you can view quantity in Point Of Sale",
                                           default=False)
    stock_product = fields.Selection([('on_hand', 'On Hand Quantity'),
                                      ('incoming_qty', 'Incoming Quantity'),
                                      ('outgoing_qty', 'Outgoing Quantity'),
                                      ('available_qty', 'Available Quantity')],
                                     string="Stock Type",
                                     help="Help you to choose the quantity you want to visible in pos")
