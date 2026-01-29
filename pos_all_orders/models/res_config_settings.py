# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    """Inherits configuration settings for set session conditions"""
    _inherit = 'res.config.settings'

    pos_all_order = fields.Selection(
        [('current_session', 'Load Orders from the current session'),
         ('past_order', 'Load All past Orders'),
         ('last_n', 'Load all orders of last n days')], string='POS all order',
        help='You can set required condition for '
             'loading the orders')
    no_of_days = fields.Integer(sring="No.of Day's", default=1,
                            help='Specify the number of days to load all of '
                                 'last n days')

    @api.model
    def get_values(self):
        """Get values from the fields"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        pos_all_order = params('pos_all_orders.pos_all_order')
        no_of_days = params('pos_all_orders.no_of_days')
        res.update(pos_all_order=pos_all_order, no_of_days=no_of_days)
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_all_orders.pos_all_order', self.pos_all_order)
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_all_orders.no_of_days', self.no_of_days)
