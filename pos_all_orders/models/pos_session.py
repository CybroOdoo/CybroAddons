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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class PosSession(models.Model):
    """Inherits pos session for getting the all orders"""
    _inherit = 'pos.session'

    def get_all_order_config(self):
        """Returns the all pos orders and orders of n days"""
        return {
            'config': self.env['ir.config_parameter'].sudo().get_param(
                'pos_all_orders.pos_all_order'),
            'no_of_days': self.env['ir.config_parameter'].sudo().get_param(
                'pos_all_orders.no_of_days')
        }

    def get_all_order(self, session_id):
        """
            Summary:
            Listing all orders in pos
            Args:
                session_id (int): current session id
            Returns: orders based on the condition

        """
        if session_id.get('session'):
            order = self.env['pos.order'].search(
                [('session_id', '=', session_id.get('session'))])
        orders = []
        if session_id.get('no_of_days'):
            now = fields.Datetime.now()
            date_to = (now + relativedelta(days=-int(session_id.get('no_of_days'))))
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
    def pos_order_partner(self, partner_id):
        """
        Summary:
        Listing orders of a partner
        Args:
            partner_id (int): selected partner id
        Returns: orders based on the partner
        """
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
