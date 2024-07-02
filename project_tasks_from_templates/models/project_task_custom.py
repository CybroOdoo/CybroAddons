# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models


class ProjectTaskCustom(models.Model):
    """Customized version of the 'project.task' model to support templates
    and sub-tasks
    Methods:
        action_open_task():
            Returns an action to open the current task in a form view"""
    _name = 'project.task.custom'
    _description = 'Project Task Custom'

    name = fields.Char(string='Name', required=True,
                       help='Enter the name of the task')
    project_template_id = fields.Many2one(
        'project.task.template', string='Project Template',
        help='Select a project task template to use for this task.')
    description = fields.Html(string='Task Description',
                              help='Enter a description for the task.')
    user_ids = fields.Many2many(
        'res.users', relation='project_task_custom_user_rel', column1='task_id',
        column2='user_id', string='Assignees', tracking=True,
        help='Select the users who are assigned to this task.')
    parent_id = fields.Many2one(
        'project.task.custom', string='Parent Task', index=True,
        help='Select the parent task, if any.')
    child_ids = fields.One2many(
        'project.task.custom', 'parent_id', string='Sub-Tasks',
        help='List of sub-tasks, if any.')
    show_tasks_page = fields.Boolean(
        compute='_compute_show_tasks_page',
        string="Show Tasks Page",
        readonly=False)

    state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked')], string='State',
        default='normal', required=True)

    def action_open_task(self):
        """ Action method to open the current task in a form view.
        Returns:
            dict: Action configuration to open the task form.
        """
        return {
            'view_mode': 'form',
            'res_model': 'project.task.custom',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }

    def _compute_show_tasks_page(self):
        """ Compute function to determine whether Sub-Tasks are enabled.
        This method computes the value of the 'show_tasks_page' field for each
        record based on whether Sub-Tasks are enabled or not. If Sub-Tasks
        are enabled, 'show_tasks_page' is set to True, allowing the display
        of Sub-Tasks. If Sub-Tasks are not enabled, 'show_tasks_page' is set
        to False.
        """
        for task in self:
            task.show_tasks_page = self.env.user.has_group(
                'project.group_subtask_project')
