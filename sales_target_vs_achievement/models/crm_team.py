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
from odoo import api, fields, models


class CrmTeam(models.Model):
    """Extend the CRM team with a team target that is calculated from the
    individual targets of its members."""
    _inherit = 'crm.team'

    target_achieve_ids = fields.One2many(
        'target.achieve', 'team_id', string="Targets",
        help="Individual targets of the salespersons of this sales team.")
    target_sale_order_ids = fields.One2many(
        'sale.order', 'team_id', string="Sales Orders", copy=False,
        help="Sales orders of this team. Used to keep the achieved amount "
             "of the targets up to date.")
    team_target = fields.Float(
        compute='_compute_team_target', store=True,
        help="Automatically calculated value for every sales team, "
             "based on the individual targets of its salespersons.")

    @api.depends('target_achieve_ids.user_target')
    def _compute_team_target(self):
        """Sum the individual targets of the salespersons of the team."""
        for team in self:
            team.team_target = sum(team.target_achieve_ids.mapped('user_target'))
