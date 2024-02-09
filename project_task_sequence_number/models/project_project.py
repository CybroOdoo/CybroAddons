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
from odoo import api, fields, models


class ProjectProject(models.Model):
    """Add sequence field to show the unique sequence, prefix field to specify
    the prefix that need to show in sequence and task sequence field for task
    entry sequence."""
    _inherit = 'project.project'

    project_prefix = fields.Char(string='Prefix',
                                 help='specify the prefix of the project')
    task_sequence_id = fields.Many2one('ir.sequence',
                                       string='Task Entry Sequence',
                                       help='Create a task entry entry '
                                            'sequence for the task for each '
                                            'project')
    project_sequence = fields.Char(string='Project Sequence', readonly=True,
                                   copy=False, default='New',
                                   help='Unique sequence number of '
                                        'the project')

    @api.model_create_multi
    def create(self, vals):
        """Overwrite the function create to calculate the sequence value based
        on the given prefix"""
        # If the project does not have any specified prefix
        for record in vals:
            if not record['project_prefix']:
                sequence = self.env['ir.sequence'].search([(
                    'code', '=', 'project.project')])
                if sequence:
                    sequence.prefix = 'PRJ/'
            # If the project have any specified prefix
            else:
                sequence = self.env['ir.sequence'].search([(
                    'code', '=', 'project.project')])
                if sequence:
                    sequence.prefix = '%s/' % record['project_prefix']
                else:
                    self.env['ir.sequence'].create({
                        'name': 'Project Project',
                        'implementation': 'standard',
                        'code': 'project.project',
                        'prefix': '%s/' % record['project_prefix']
                    })
            project_task_sequence = self.env['ir.sequence'].create({
                'name': 'Task %s' % (record['name']),
                'implementation': 'standard'})
            record['task_sequence_id'] = project_task_sequence.id
            record['project_sequence'] = self.env['ir.sequence'].next_by_code(
                'project.project')
            return super(ProjectProject, self).create(record)
        return

    def write(self, vals):
        """Overwrite the function to update the sequence """
        if vals.get('project_prefix'):
            sequence = self.env['ir.sequence'].search([('code', '=',
                                                        'project.project')])
            if sequence:
                sequence.prefix = '%s/' % vals['project_prefix']
                vals['project_sequence'] = self.env[
                    'ir.sequence'].next_by_code('project.project')
        return super(ProjectProject, self).write(vals)
