# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProjectTask(models.Model):
    """Extend project.task to generate hierarchical task sequence numbers."""
    _inherit = 'project.task'

    task_sequence = fields.Char(
        string='Task Sequence',
        readonly=True,
        copy=False,
        default='New',
        help='Hierarchical sequence number of the task.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            task.with_context(
                bypass_sequence=True
            )._compute_custom_sequence()
        return tasks

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get('bypass_sequence'):
            for task in self:
                task.with_context(
                    bypass_sequence=True
                )._compute_custom_sequence()
        return result

    def _compute_custom_sequence(self):
        """Compute hierarchical sequence for tasks."""
        for task in self:

            if not task.project_id or not task.project_id.project_sequence:
                continue

            if task.parent_id:
                parent_seq = task.parent_id.task_sequence or task.parent_id.name
                subtask_number = task._get_sibling_count(
                    task.parent_id
                )
                sequence = f"{parent_seq}/Sub Task {subtask_number}"

            else:
                task_number = task._get_task_count(
                    task.project_id
                )
                formatted_task_number = str(task_number).zfill(4)

                seq = self.env['ir.sequence'].search(
                    [('code', '=', 'project.task')],
                    limit=1
                )

                task_prefix = seq.prefix if seq else ''

                sequence = (
                    f"{task.project_id.project_sequence}-"
                    f"{task_prefix}{formatted_task_number}"
                )

            # Avoid recursion
            task.sudo().write({'task_sequence': sequence})

    def _get_task_count(self, project):
        """Return number of root tasks in the project."""
        return self.search_count([
            ('project_id', '=', project.id),
            ('parent_id', '=', False)
        ])

    def _get_sibling_count(self, parent_task):
        """Return number of sibling subtasks under the parent task."""
        return self.search_count([
            ('parent_id', '=', parent_task.id),
            ('id', '!=', self.id)
        ]) + 1
