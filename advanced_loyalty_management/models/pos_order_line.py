# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, fields


class PosOrderLine(models.Model):
    """To Show the redeemed points in the redemption history"""
    _inherit = 'pos.order.line'

    points_remaining = fields.Float(string="Points Remaining",
                                    help="Remaining points after claming the "
                                         "reward")

    @api.model
    def remaining_points(self, balance, token):
        """Remaining points calculated after claiming the reward"""
        order = self.env['pos.order'].search([('uuid', '=', token[0])], limit=1)
        if not order:
            return
            
        pos_order_lines = self.env['pos.order.line'].search(
            [('is_reward_line', '=', True), ('order_id', '=', order.id)])
        
        if not pos_order_lines:
            pos_order_lines = order.lines
            
        pos_order_lines.write({'points_remaining': balance[0]})


        card = self.env['loyalty.card'].search([('partner_id', '=', order.partner_id.id)], limit=1)
        if card:
             self.env['loyalty.history'].create({
                'card_id': card.id,
                'order_model': 'pos.order',
                'order_id': order.id,
                'description': f"Points redeemed in order {order.name}",
                'used': sum(order.lines.mapped('points_cost')),
                'issued': 0,
             })
