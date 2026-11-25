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


class AccountMove(models.Model):
    """Extends account.move to link related voice assistant calls."""
    _inherit = 'account.move'

    voice_call_count = fields.Integer(
        string="Voice Calls",
        compute='_compute_voice_call_count',
        help="Number of voice calls associated with this invoice."
    )

    def _compute_voice_call_count(self):
        call_data = self.env['ora.call.history']._read_group(
            [('invoice_id', 'in', self.ids)],
            ['invoice_id'],
            ['__count']
        )
        mapped_counts = {invoice.id: count for invoice, count in call_data}
        for move in self:
            move.voice_call_count = mapped_counts.get(move.id, 0)

    def action_view_voice_calls(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Voice Calls'),
            'res_model': 'ora.call.history',
            'view_mode': 'list,form',
            'domain': [('invoice_id', '=', self.id)],
            'context': {'default_invoice_id': self.id},
        }

