# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """This model extends the base configuration settings for Point of Sale
     configurations."""
    _name = 'res.config.settings'
    _inherit = ['res.config.settings', 'pos.load.mixin']

    allow_customer_screen = fields.Boolean(string="Customer Screen",
                                           related="pos_config_id.allow_customer_screen",
                                           readonly=False,
                                           help='Allows the screen share with '
                                                'the customers')
    allow_product_click = fields.Boolean(string="Allow Product Click",
                                         related="pos_config_id.allow_product_click",
                                         readonly=False,
                                         help='Allows the customer to set '
                                              'screen open when click product')

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Returns the list of fields to be loaded for POS data."""
        return [
            'allow_product_click','allow_customer_screen'
        ]
