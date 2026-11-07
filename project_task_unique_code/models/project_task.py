# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProjectTask(models.Model):
    """Stamp each task with a unique code from its project's sequence."""
    _inherit = 'project.task'

    unique_code = fields.Char(readonly=True, copy=False,
                              help='Unique code of the task, made from the project short code.')

    _unique_code_company_uniq = models.UniqueIndex(
        '(unique_code, COALESCE(company_id, 0))',
        'The task code must be unique per company.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Give each new task of a project its unique code."""
        tasks = super().create(vals_list)
        tasks._assign_unique_code()
        return tasks

    def write(self, vals):
        """A task moved into a project without a code gets one."""
        res = super().write(vals)
        if vals.get('project_id'):
            self._assign_unique_code()
        return res

    def _assign_unique_code(self):
        """Draw the next code for tasks that have a project but no code yet.

        Runs as superuser: the code is system-generated, and portal
        collaborators (project sharing) can neither read sequences nor
        write this field.
        """
        for task in self.sudo().filtered(lambda t: not t.unique_code and t.project_id.sequence_id):
            task.unique_code = task.project_id.sequence_id.next_by_id()
