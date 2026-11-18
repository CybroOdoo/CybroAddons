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
from odoo import api, fields, models


class MaintenanceTeam(models.Model):
    """Model that handles the maintenance team """
    _inherit = "maintenance.team"

    is_hotel = fields.Boolean(string="Is Hotel Maintenance", default=False)
    user_id = fields.Many2one('res.users', string='Team Leader',
                              help="Leader of Team")
    domain_leader_ids = fields.Many2many(
        'res.users', string="Allowed Team Leaders",
        compute='_compute_domain_user_ids',
        help="Users allowed to lead a hotel maintenance team")
    domain_member_ids = fields.Many2many(
        'res.users', string="Allowed Members",
        compute='_compute_domain_user_ids',
        help="Users allowed to be members of a hotel maintenance team")

    @api.depends('is_hotel')
    def _compute_domain_user_ids(self):
        """Compute the users selectable as leader or member. The hotel
        groups are only applied through the hotel views, so the standard
        Maintenance team fields keep their original behaviour."""
        leader_group = self.env.ref(
            'hotel_management_odoo.maintenance_team_group_leader')
        member_group = self.env.ref(
            'hotel_management_odoo.maintenance_team_group_user')
        leaders = self.env['res.users'].search(
            [('group_ids', 'in', leader_group.ids)])
        members = self.env['res.users'].search(
            [('group_ids', 'in', member_group.ids)])
        for team in self:
            team.domain_leader_ids = leaders
            team.domain_member_ids = members
