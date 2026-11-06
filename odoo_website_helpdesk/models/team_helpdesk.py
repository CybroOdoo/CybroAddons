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


class TeamHelpDesk(models.Model):
    """Helpdesk team"""
    _name = 'team.helpdesk'
    _description = 'Helpdesk Team'

    name = fields.Char(required=True, help='Helpdesk Team Name')
    team_lead_id = fields.Many2one('res.users', string='Team Leader',
                                   help='Team Leader Name',
                                   domain=[('share', '=', False)])
    member_ids = fields.Many2many('res.users', string='Members',
                                  help='Team Members',
                                  domain=[('share', '=', False)])
    email = fields.Char(help='Email of the team.')
    project_id = fields.Many2one('project.project',
                                 help='Project of the tasks created from the '
                                      'tickets of the team.')
    create_task = fields.Boolean(help="Create tasks from the tickets of the "
                                      "team")

    def _add_helpdesk_groups(self):
        """Give the helpdesk access to the leader and the members"""
        leader_group = self.env.ref(
            'odoo_website_helpdesk.helpdesk_team_leader')
        user_group = self.env.ref('odoo_website_helpdesk.helpdesk_user')
        leaders = self.team_lead_id.filtered(
            lambda user: leader_group not in user.all_group_ids)
        members = self.member_ids.filtered(
            lambda user: user_group not in user.all_group_ids)
        if leaders:
            leader_group.sudo().write(
                {'user_ids': [(4, user.id) for user in leaders]})
        if members:
            user_group.sudo().write(
                {'user_ids': [(4, user.id) for user in members]})

    @api.model_create_multi
    def create(self, vals_list):
        """Give the helpdesk access to the team"""
        teams = super().create(vals_list)
        teams._add_helpdesk_groups()
        return teams

    def write(self, vals):
        """Give the helpdesk access to the new leader and members"""
        result = super().write(vals)
        if 'team_lead_id' in vals or 'member_ids' in vals:
            self._add_helpdesk_groups()
        return result
