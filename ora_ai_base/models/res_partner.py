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


class ResPartner(models.Model):
    """Extends res.partner to link related voice assistant calls."""
    _inherit = 'res.partner'

    voice_call_count = fields.Integer(
        string="Voice Calls",
        compute='_compute_voice_call_count',
        help="Number of voice calls associated with this contact."
    )

    def _compute_voice_call_count(self):
        call_data = self.env['ora.call.history']._read_group(
            ['|', ('partner_id', 'in', self.ids), ('created_partner_id', 'in', self.ids)],
            ['partner_id'],
            ['__count']
        )
        mapped_counts = {partner.id: count for partner, count in call_data}
        for partner in self:
            partner.voice_call_count = mapped_counts.get(partner.id, 0)

    def action_view_voice_calls(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Voice Calls'),
            'res_model': 'ora.call.history',
            'view_mode': 'list,form',
            'domain': ['|', ('partner_id', '=', self.id), ('created_partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

