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


class ResConfigSettings(models.TransientModel):
    """ Inherit the base settings to add field. """
    _inherit = 'res.config.settings'

    display_stock = fields.Boolean(string="Display Stock",
                                   readonly=False, help="By enabling you can "
                                                        "view quantity in Point Of Sale",
                                   default=False, config_parameter='pos_product_stock.display_stock')
    stock_type = fields.Selection(related='pos_config_id.stock_product',
                                  string="Stock Type", readonly=False,
                                  required=True, help="Help you to choose "
                                                      "the quantity you want to visible in pos")
    stock_from = fields.Selection(related='pos_config_id.location_from',
                                  string="Show Stock Of", readonly=False,
                                  required=True, help="can choose the location "
                                                      "where you want to display the stock ")
    stock_location_id = fields.Many2one(related='pos_config_id.pos_stock_location_id',
                                        string="Stock Location", readonly=False,
                                        help="This field helps to hold the location")
