# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class ProjectProject(models.Model):
    """
    Extends the 'project.project' model to allow creating projects
    from task templates.

    Fields:
        project_template_id (Many2one): Select a project task template to
        generate tasks for this project.

    Methods:
        action_create_project_from_template():
            Creates tasks for the project based on the selected template.
        _create_task(item, parent):
            Creates a project task (and its subtasks) without stage linkage.
        _create_task_with_stage(item, stage, parent):
            Creates a project task (and its subtasks) with a given stage.
    """
    _inherit = 'project.project'

    project_template_id = fields.Many2one(
        comodel_name='project.task.template',
        string='Project Template',
        help='Select a project task template to use for this project.')

    def action_create_project_from_template(self):
        """
        Create project tasks from the selected template.

        Returns:
            dict: Action to open the project form view.
        """
        if not self.project_template_id.stage_ids:
            # Create tasks directly from the template
            for item in self.project_template_id.task_ids:
                self._create_task(item, parent=False)
            return {
                'view_mode': 'form',
                'res_model': 'project.project',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'context': self._context,
            }

        # Create tasks grouped by stages
        for stage in self.project_template_id.stage_ids:
            if self.id not in stage.project_stage_id.project_ids.ids:
                stage.project_stage_id.project_ids = [(4, self.id)]

            for task in stage.task_ids:
                self._create_task_with_stage(
                    task, stage.project_stage_id, parent=False
                )

    def _create_task(self, item, parent):
        """
        Create a new project task and its subtasks without stage linkage.

        Args:
            item (recordset): Task template record.
            parent (int|bool): ID of the parent task, or False for top-level.
        """
        task = self.env['project.task'].sudo().create({
            'project_id': self.id,
            'name': item.name,
            'parent_id': parent,
            'stage_id': self.env['project.task.type']
                         .search([('sequence', '=', 1)], limit=1).id,
            'user_ids': item.user_ids,
            'description': item.description,
            'state': item.state or '01_in_progress',
        })

        for sub_task in item.child_ids:
            self._create_task(sub_task, parent=task.id)

    def _create_task_with_stage(self, item, stage, parent=False):
        """
        Create a new project task and its subtasks with a specific stage.

        Args:
            item (recordset): Task template record.
            stage (recordset): Project task stage.
            parent (int|bool): ID of the parent task, or False for top-level.
        """
        task = self.env['project.task'].sudo().create({
            'project_id': self.id,
            'name': item.name,
            'parent_id': parent,
            'stage_id': stage.id,
            'user_ids': item.user_ids,
            'description': item.description,
            'state': item.state or '01_in_progress',
        })

        for sub_task in item.child_ids:
            self._create_task_with_stage(sub_task, stage, parent=task.id)
