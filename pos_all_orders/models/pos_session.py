# -*- coding: utf-8 -*-
################################################################################
#    POS ALL Order
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        result += {
            'pos.order', 'pos.order.line'
        }
        return result

    def _loader_params_pos_order(self):
        return {'search_params': {
            'domain': [],
            'fields': ['name', 'date_order', 'pos_reference',
                       'partner_id', 'lines']}}

    def _get_pos_ui_pos_order(self, params):
        return self.env['pos.order'].search_read(**params['search_params'])

    def _loader_params_pos_order_line(self):
        return {'search_params': {'domain': [],
                                  'fields': ['product_id', 'qty',
                                             'price_subtotal', 'total_cost']}}

    def _get_pos_ui_pos_order_line(self, params):
        return self.env['pos.order.line'].search_read(
            **params['search_params'])

    def get_all_order_config(self):
        return {
            'config': self.env['ir.config_parameter'].sudo().get_param('pos_all_orders.pos_all_order'),
            'n_days': self.env['ir.config_parameter'].sudo().get_param('pos_all_orders.n_days')
        }

    def get_all_order(self, session_id):
        if session_id.get('session'):
            order = self.env['pos.order'].search(
                [('session_id', '=', session_id.get('session'))])
        orders = []
        if session_id.get('n_days'):
            now = fields.Datetime.now()
            date_to = (now + relativedelta(days=-int(session_id.get('n_days'))))

            order = self.env['pos.order'].search(
                [('date_order', '>=', date_to)])
        for rec in order:
            orders.append(
                {'id': rec.id, 'name': rec.name, 'date_order': rec.date_order,
                 'pos_reference': rec.pos_reference,
                 'partner_id': rec.partner_id.name,
                 'session': 'current_session'
                 })
        return orders

    def pos_order_partner(self, partner_id):
        order = self.env['pos.order'].search(
            [('partner_id', '=', partner_id)])
        orders = []
        for rec in order:
            orders.append(
                {'id': rec.id, 'name': rec.name, 'date_order': rec.date_order,
                 'pos_reference': rec.pos_reference,
                 'partner_id': rec.partner_id.name,
                 })
        return orders


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_all_order = fields.Selection(
        [('current_session', 'Load Orders from the current session'),
         ('past_order', 'Load All past Orders'),
         ('last_n', 'Load all orders of last n days')])

    n_days = fields.Integer("No.of Day's")

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
