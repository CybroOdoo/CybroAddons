# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    """ Inheriting project_task model to add sprint features """
    _inherit = 'project.task'

    sprint_id = fields.Many2one('project.sprint', string="Sprint",
                                help="Sprint",
                                domain="[('project_id', '=', project_id)]")
    linked_issue = fields.Selection(string="Linked issue", selection=[
        ('is_blocked_by', 'Is blocked by')], help="Linked Issue")
    issue_task_id = fields.Many2one('project.task', string="Task",
                                    help="Task")

    @api.constrains('stage_id')
    def _check_stage_id(self):
        """ Blocking stage change when there is a linked issue """
        if self.linked_issue:
            raise UserError(_(
                "This task is linked to another task and cannot be modified."))
        else:
            pass
