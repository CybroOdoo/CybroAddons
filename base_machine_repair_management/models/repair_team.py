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


class RepairTeam(models.Model):
    """This is used to set the repair team"""
    _name = 'repair.team'
    _description = 'Repair Team'
    _rec_name = "team_name"

    team_name = fields.Char(string='Name', help="Name of the Team", required=True)
    team_lead_id = fields.Many2one('hr.employee',
                                   string="Team Lead",
                                   help="Team lead of the team", required=True)

    repair_work_ids = fields.Many2many('machine.repair',
                                       string='Repair Reference', readonly=True,
                                       help='Reference of the machine repair')
    member_ids = fields.One2many('team.member',
                                 'inverse_id', string="Members",
                                 help="Team members pof the repair team")
