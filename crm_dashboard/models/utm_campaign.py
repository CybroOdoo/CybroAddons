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
#############################################################################
from odoo import fields, models


class CampaignSmartButton(models.Model):
    """Extends the UTM Campaign model with a Smart Button to calculate and
    display the Win Loss Ratio."""
    _inherit = 'utm.campaign'

    total_ratio = fields.Float(compute='_compute_ratio',
                               help="Total lead ratio")

    def get_ratio(self):
        """Open the won and lost leads of the campaign upon clicking the
        Smart Button.
        Returns:
            dict: A dictionary specifying the action to be taken upon button
            click."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Win Loss Ratio',
            'view_mode': 'kanban',
            'res_model': 'crm.lead',
            'domain': [['campaign_id', '=', self.id], "|",
                       "&", ["active", "=", True], ["probability", '=', 100],
                       "&", ["active", "=", False], ["probability", '=', 0]
                       ],
            'context': "{'create': False,'records_draggable': False}"
        }

    def _compute_ratio(self):
        """Compute the Win Loss Ratio of the campaign's leads."""
        for campaign in self:
            total_won = self.env['crm.lead'].search_count(
                [('active', '=', True), ('probability', '=', 100),
                 ('campaign_id', '=', campaign.id)])
            total_lose = self.env['crm.lead'].search_count(
                [('active', '=', False), ('probability', '=', 0),
                 ('campaign_id', '=', campaign.id)])
            campaign.total_ratio = round(
                total_won / total_lose, 2) if total_lose else 0
