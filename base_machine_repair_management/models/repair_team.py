"""Repair Team"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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


class RepairTeam(models.Model):
    """This is used to set the repair team"""
    _name = 'repair.teams'
    _description = 'Repair Teams'
    _rec_name = "team_name"

    team_name = fields.Char(string='Name', help="Name of the Team")
    team_lead_id = fields.Many2one('hr.employee',
                                   string="Team Lead",
                                   help="Team lead of the team")
    repair_work_id = fields.Many2one('machine.repair',
                                     string='Repair Reference',
                                     help='Reference of the machine repair')
    member_ids = fields.One2many('team.members',
                                 'inverse_id', string="Members",
                                 help="Team members pof the repair team")


class TeamMembers(models.Model):
    """This is used for the team members of repair team"""
    _name = 'team.members'
    _description = 'Team Members'
    _rec_name = 'member_id'

    inverse_id = fields.Many2one('repair.teams', string="Repair Teams",
                                 help="Repair teams for machine")
    member_id = fields.Many2one('hr.employee', string="Member",
                                help="member of the repair team")
    login = fields.Char(related='member_id.work_email', string="Login",
                        help="Login details for member")
