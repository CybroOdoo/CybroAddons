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


class SurveyTeamMember(models.Model):
    """Class for Survey Team Member"""
    _name = "survey.team.member"
    _description = "Survey Team Member"
    _rec_name = 'member_id'

    member_id = fields.Many2one('res.users', string="Name", required=True, help="Name of the team member")
    phone = fields.Char(string="Phone", help="Phone number of the team member", related='member_id.partner_id.phone')
    email = fields.Char(string="Email", help="Email address of the team member", related='member_id.partner_id.email')
    survey_team_id = fields.Many2one('survey.team', string="Survey Team", help="The survey team this member belongs to")
