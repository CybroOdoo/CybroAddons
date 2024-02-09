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


class ProjectTask(models.Model):
    """In ProjectTask class, which will add a new field for task sequence.
       When we create the record, the sequence will be based on the
      task_sequence."""
    _inherit = 'project.task'

    task_sequence = fields.Char(string='Task Sequence', readonly=True,
                                copy=False, default='New',
                                help='Unique sequence number of the task.')

    @api.model_create_multi
    def create(self, vals):
        """Overwrite the function create to calculate the sequence value based
         on the given prefix"""
        for records in vals:
            if not records['project_id']:
                if records.get('task_sequence', 'New') == 'New':
                    records['task_sequence'] = self.env['ir.sequence']. \
                                                   next_by_code(
                        'project.task') or 'New'
            else:
                project = self.env['project.project'].browse(
                    records['project_id'])
                if project.task_sequence_id.prefix:
                    records['task_sequence'] = '%s/%s/%s' % \
                                             (project.project_sequence,
                                              project.task_sequence_id.prefix,
                                              self.env['ir.sequence'].
                                               next_by_code('project.task') or
                                              'New')
                else:
                    records['task_sequence'] = '%s/%s' % \
                                                  (project.project_sequence,
                                                   self.env['ir.sequence'].
                                                   next_by_code(
                                                       'project.task') or
                                                   'New')
            return super(ProjectTask, self).create(records)

    def write(self, vals):
        """Overwrite the function to update the sequence """
        if vals.get('project_id'):
            project = self.env['project.project'].browse(vals.get(
                'project_id'))
            if project.task_sequence_id.prefix:
                vals['task_sequence'] = '%s/%s/%s' % \
                                        (project.project_sequence,
                                         project.task_sequence_id.prefix,
                                         self.env['ir.sequence'].next_by_code(
                                             'project.task') or 'New')
            else:
                vals['task_sequence'] = '%s/%s' % \
                                        (project.project_sequence,
                                         self.env['ir.sequence'].
                                         next_by_code('project.task') or 'New')
        return super(ProjectTask, self).write(vals)
