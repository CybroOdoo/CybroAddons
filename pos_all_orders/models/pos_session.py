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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class PosSession(models.Model):
    """inherit pos.session to load data in session."""
    _inherit = 'pos.session'

    @api.model
    def get_all_order_config(self):
        """Retrieves the configuration parameters related to POS all orders."""
        return {
            'config': self.env['ir.config_parameter'].sudo().get_param('pos_all_orders.pos_all_order'),
            'n_days': self.env['ir.config_parameter'].sudo().get_param('pos_all_orders.n_days')
        }

    @api.model
    def get_all_order(self, session_id):
        """Retrieves POS orders based on the provided session ID and optional number of days."""
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

    @api.model
    def get_all_past_orders(self,session_id):
        """Get all past orders up to the current date."""
        if session_id.get('session'):
            order = self.env['pos.order'].search(
                [('session_id', '=', session_id.get('session'))])
        orders = []
        current_date = fields.Datetime.now()
        order = self.env['pos.order'].search([
            ('date_order', '<=', current_date),
            ('state', 'not in', ['draft', 'cancel'])
        ])
        for rec in order:
            orders.append(
                {'id': rec.id, 'name': rec.name, 'date_order': rec.date_order,
                 'pos_reference': rec.pos_reference,
                 'partner_id': rec.partner_id.name,
                 'session': 'past_order'
                 })
        return orders

    @api.model
    def get_default_all_orders(self,session_id):
        """Retrieves all POS orders."""
        if session_id.get('session'):
            order = self.env['pos.order'].search([])
        all_orders = []
        for rec in order:
            all_orders.append({
                'id': rec.id,
                'name': rec.name,
                'date_order': rec.date_order,
                'pos_reference': rec.pos_reference,
                'partner_id': rec.partner_id.name,
                'session': rec.session_id
            })
        return all_orders
