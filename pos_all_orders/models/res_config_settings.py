# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Inherit the base settings to add field."""
    _name = 'res.config.settings'
    _inherit = ['res.config.settings','pos.load.mixin']

    pos_all_order = fields.Selection(
        [('current_session', 'Load Orders from the current session'),
         ('past_order', 'Load All past Orders'),
         ('last_n', 'Load all orders of last n days')],help='Select Order types')

    n_days = fields.Integer(string="No.of Day's",help='Add number of days')

    @api.model
    def get_values(self):
        """get values from the fields"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        pos_all_order = params('pos_all_orders.pos_all_order')
        n_days = params('pos_all_orders.n_days')
        res.update(
            pos_all_order=pos_all_order,
            n_days=n_days
        )
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_all_orders.pos_all_order', self.pos_all_order)
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_all_orders.n_days',
            self.n_days)
