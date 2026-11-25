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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """Extends sale.order to link related voice assistant calls."""
    _inherit = 'sale.order'

    voice_call_count = fields.Integer(
        string="Voice Calls",
        compute='_compute_voice_call_count',
        help="Number of voice calls associated with this sale order."
    )

    def _compute_voice_call_count(self):
        call_data = self.env['ora.call.history']._read_group(
            [('order_id', 'in', self.ids)],
            ['order_id'],
            ['__count']
        )
        mapped_counts = {order.id: count for order, count in call_data}
        for order in self:
            order.voice_call_count = mapped_counts.get(order.id, 0)

    def action_view_voice_calls(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Voice Calls'),
            'res_model': 'ora.call.history',
            'view_mode': 'list,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

