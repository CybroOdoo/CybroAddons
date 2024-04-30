"""Repair Team"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
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
from odoo import fields, models


class TeamMember(models.Model):
    """This is used for the team members of repair team"""
    _name = 'team.member'
    _description = 'Team Member'
    _rec_name = 'member_id'

    inverse_id = fields.Many2one('repair.team', string="Repair Team",
                                 help="Repair team for machine")
    member_id = fields.Many2one('hr.employee', string="Member",
                                help="member of the repair team")
    login = fields.Char(related='member_id.work_email', string="Login",
                        help="Login details for member")
