# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class HelpDeskTeam(models.Model):
    """Helpdesk team"""
    _name = 'help.team'
    _description = 'Helpdesk Team'

    name = fields.Char('Name', help='Helpdesk Team Name')
    team_lead_id = fields.Many2one('res.users', string='Team Leader',
                                   help='Team Leader Name',
                                   domain=lambda self: [
                                       ('groups_id', 'in', self.env.ref(
                                           'odoo_website_helpdesk.helpdesk_team_leader').id)])
    member_ids = fields.Many2many('res.users', string='Members',
                                  help='Team Members',
                                  domain=lambda self: [
                                      ('groups_id', 'in', self.env.ref(
                                          'odoo_website_helpdesk.helpdesk_user').id)])
    email = fields.Char('Email', help='Email')
    project_id = fields.Many2one('project.project',
                                 string='Project',
                                 help='Projects')
    create_task = fields.Boolean(string="Create Task",
                                 help="Task created or not")

    @api.onchange('team_lead_id')
    def members_choose(self):
        """Members selection function"""
        fetch_memebers = self.env['res.users'].search([])
        filterd_members = fetch_memebers.filtered(
            lambda x: x.id != self.team_lead_id.id)
        return {'domain': {'member_ids':
                               [('id', '=', filterd_members.ids), (
                               'groups_id', 'in',
                               self.env.ref('base.group_user').id),
                                ('groups_id', 'not in', self.env.ref(
                                    'odoo_website_helpdesk.helpdesk_team_leader').id)]}}
