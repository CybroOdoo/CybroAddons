# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Naveen K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

"""Module Containing Checklist data"""
from odoo import models, fields


class StageCheckListLines(models.Model):
    _name = "stage.check.list"
    _description = "Stage Based CheckList"
    _rec_name = 'check_task'

    check_task = fields.Char(string="Task", required=True)
    s_team_id = fields.Many2one('crm.team', string="Selected Teams")
    approve_groups = fields.Many2many('res.groups',
                                      string="User Groups",
                                      help="only these user groups may "
                                           "approve the item")
    stage_recover = fields.Boolean(default=False,
                                   string="Saved",
                                   help="If checked the item will be "
                                        "recoverable for leads on this "
                                        "stage.Otherwise the item must be "
                                        "approved each time when lead is on "
                                        "this stage")
    stage_id = fields.Many2one('crm.stage', string="Stage")
