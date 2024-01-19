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


class ProjectSubTask(models.Model):
    """Customized version of the 'project.task' model to support templates
    and sub-tasks
    Methods:
        action_open_task():
            Returns an action to open the current task in a form view"""
    _name = 'project.sub.task'
    _description = 'Project Sub Task'

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
        'project.sub.task', string='Parent Task', index=True,
        help='Select the parent task, if any.')
    child_ids = fields.One2many(
        'project.sub.task', 'parent_id', string='Sub-Tasks',
        help='List of sub-tasks, if any.')
    show_tasks_page = fields.Boolean(
        compute='_compute_show_tasks_page',
        string="Show Tasks Page",
        readonly=False)

    def action_open_task(self):
        """ Action method to open the current task in a form view.
        Returns:
            dict: Action configuration to open the task form.
        """
        return {
            'view_mode': 'form',
            'res_model': 'project.sub.task',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }

    def _compute_show_tasks_page(self):
        """ Compute function to determine whether project_template_id present.
        This method computes the value of the 'show_tasks_page' field for each
        record based on whether project_template_id present or not. If project_template_id
        present, 'show_tasks_page' is set to True, allowing the display
        of Sub-Tasks. If project_template_id are not present, 'show_tasks_page'
        is set to False.
        """
        for task in self:
            if task.project_template_id:
                task.show_tasks_page = True
