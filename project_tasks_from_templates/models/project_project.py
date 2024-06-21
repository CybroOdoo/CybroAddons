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


class ProjectProject(models.Model):
    """ This class extends the 'project.project' model to add a many2one
    field for selecting project task template.
    Methods:
        action_create_project_from_template():
            Creates a new project based on the selected project template.
        _create_task(item, parent):
            Creates a new project task for the given item and attaches
            it to the current project.
    """
    _inherit = 'project.project'

    project_template_id = fields.Many2one(
        'project.task.template',
        string='Project Template',
        help='Select a project task template to use for this project.')

    def action_create_project_from_template(self):
        """ Creates a new project based on the selected project template.
        Returns:
            dict: Action configuration to open the project form.
        """
        if not self.project_template_id.stage_ids:
            for item in self.project_template_id.task_ids:
                self._create_task(item, False)
            return {
                'view_mode': 'form',
                'res_model': 'project.project',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'context': self._context
            }
        else:
            for item in self.project_template_id.stage_ids:
                if self.id not in item.project_stage_id.project_ids.ids:
                    item.project_stage_id.project_ids = [(4, self.id)]
                for task in item.task_ids:
                    self._create_task_with_stage(task, item.project_stage_id,
                                                 False)

    def _create_task(self, item, parent):
        """Creates a new project task for the given item and attaches it to
        the current project.
        Args:
            item (models.Model): project task
            parent (int): id of parent project task
        """

        task = self.env['project.task'].sudo().create({
            'project_id': self.id,
            'name': item.name,
            'parent_id': parent,
            'stage_id': self.env['project.task.type'].search(
                [('sequence', '=', 1)], limit=1).id,
            'user_ids': item.user_ids,
            'description': item.description,
            'state': item.state or '01_in_progress',
        })
        for sub_task in item.child_ids:
            self._create_task(sub_task, task.id)

    def _create_task_with_stage(self, item, stage, parent=False):
        """Creates a new project task with stage for the given item and attaches it to
        the current project.
        Args:
            item (models.Model): project task
            parent (int): id of parent project task
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
            self._create_task_with_stage(sub_task, stage, task.id)
