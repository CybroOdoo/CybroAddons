# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
    """This model is used to define repair teams responsible for handling machine repairs."""
    _name = 'repair.team'
    _description = 'Repair Team'
    _rec_name = "team_name"

    team_name = fields.Char(string='Name',
                            help="The name of the repair team.", required=True)
    team_lead_id = fields.Many2one('hr.employee', string="Team Lead",
                                   help="The leader of the repair team.",
                                   required=True)
    repair_work_ids = fields.Many2many('machine.repair', string='Repair Reference',
                                       readonly=True,
                                       help="References to machine repairs assigned to the team.")
    member_ids = fields.One2many('team.member', 'inverse_id',
                                 string="Members", copy=False,
                                 help="Members assigned to the repair team.")
