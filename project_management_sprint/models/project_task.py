# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    """ Inheriting project_task model to add sprint features """
    _inherit = 'project.task'

    sprint_id = fields.Many2one('project.sprint', string="Sprint",
                                help="Select the sprint in which this task "
                                     "will be planned or executed.",
                                domain="[('project_id', '=', project_id)]")
    linked_issue = fields.Selection(string="Linked issue", selection=[
        ('is_blocked_by', 'Is blocked by')],
        help="Indicates that this task is blocked by another task.")
    issue_task_id = fields.Many2one('project.task', string="Task",
                                    help="Select the task that is blocking "
                                         "the progress of this task.")

    def write(self, vals):
        """Block stage changes for tasks that are blocked by another task."""
        if 'stage_id' in vals:
            for task in self:
                if task.linked_issue:
                    raise UserError(_(
                        "This task is linked to another task and cannot be "
                        "moved to another stage."))
        return super().write(vals)
