# -*- coding: utf-8 -*-
###################################################################################
#
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Akhil(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

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
