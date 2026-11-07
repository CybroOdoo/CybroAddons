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
import re

from odoo import api, fields, models


class ProjectProject(models.Model):
    """Add a short code and a task sequence to projects."""
    _inherit = 'project.project'

    project_short_code = fields.Char(
        string='Short Code', copy=False,
        help="Short code used as the prefix of the unique code of the project's tasks. "
             "Projects created without one get a code made from their name.")
    sequence_id = fields.Many2one(
        'ir.sequence', string='Reference Sequence', check_company=True, copy=False, readonly=True,
        help="Sequence that numbers the project's tasks.")

    # COALESCE: most projects have no company, and NULLs never clash in a plain unique.
    _project_short_code_company_uniq = models.UniqueIndex(
        '(project_short_code, COALESCE(company_id, 0))',
        'The project code must be unique per company.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Give each new project a short code and a task sequence."""
        projects = super().create(vals_list)
        projects._ensure_task_code_sequence()
        return projects

    def write(self, vals):
        """Keep the sequence prefix in line with the short code."""
        res = super().write(vals)
        if 'project_short_code' in vals and not self.env.context.get('task_code_sync'):
            self._ensure_task_code_sequence()
        return res

    def _ensure_task_code_sequence(self):
        """Set a short code when missing and a sequence whose prefix is that code."""
        Sequence = self.env['ir.sequence'].sudo()
        for project in self.with_context(task_code_sync=True):
            if not project.project_short_code:
                project.project_short_code = project._default_short_code()
            prefix = project.project_short_code + '-'
            if not project.sequence_id:
                project.sequence_id = Sequence.create({
                    'name': self.env._("%(project)s Project Sequence", project=project.name),
                    'prefix': prefix,
                    'padding': 3,
                    'company_id': project.company_id.id,
                })
            elif project.sequence_id.prefix != prefix:
                project.sequence_id.sudo().prefix = prefix

    def _default_short_code(self):
        """Code made from the project name, unique within the project's company."""
        self.ensure_one()
        base = re.sub(r'[^A-Za-z0-9]', '', self.name or '').upper()[:4] or 'PRJ'
        code, number = base, 1
        Project = self.with_context(active_test=False)
        while Project.search_count([
            ('project_short_code', '=', code),
            ('company_id', '=', self.company_id.id),
            ('id', '!=', self.id),
        ]):
            number += 1
            code = f'{base}{number}'
        return code
