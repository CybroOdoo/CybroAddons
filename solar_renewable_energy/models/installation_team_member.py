# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amrithesh K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class InstallationTeamMember(models.Model):
    """Class for solar installation team member"""
    _name = "installation.team.member"
    _description = "Installation Team Member"
    _rec_name = 'member_id'

    member_id = fields.Many2one('res.users', string="Name", required=True, help="Name of the team member")
    phone = fields.Char(string="Phone", help="Phone number of the team member", related='member_id.partner_id.phone')
    email = fields.Char(string="Email", help="Email address of the team member", related='member_id.partner_id.email')
    installation_team_id = fields.Many2one('installation.team', string="Installation Team", help="The Installation team this member belongs to")
