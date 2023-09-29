# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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
from odoo import fields, models


class StageCheckList(models.Model):
    """Model for stage-based checklist lines."""
    _name = "stage.check.list"
    _description = "Stage Based CheckList"
    _rec_name = 'check_task'

    check_task = fields.Char(string="Task", required=True,
                             help="Char field representing the task associated"
                                  " with the checklist item.")
    sales_team_id = fields.Many2one('crm.team', string="Selected Teams",
                                    help="Many2one field representing the "
                                         "selected team associated with the"
                                         " checklist item.")
    approve_groups_ids = fields.Many2many('res.groups', string="User Groups",
                                          help="Only these user groups may "
                                               "approve "
                                               "the item")
    is_stage_recover = fields.Boolean(default=False, string="Saved",
                                      help="If checked, item will be recoverable"
                                           " for leads on this stage. Otherwise, "
                                           "the item must be approved each time "
                                           "when the lead is on this stage.")
    stage_id = fields.Many2one('crm.stage', string="Stage",
                               help="Many2one field representing the "
                                    "associated stage.")
