# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class IrAttachment(models.Model):
    """Inherit IR attachment for adding extra fields and inheriting create
    function """
    _inherit = 'ir.attachment'

    attach_to = fields.Selection([('project', 'Project'),
                                  ('task', 'Task')],
                                 required=True, string="Attach To",
                                 help="if Project, file attached to Project."
                                      " Otherwise to task.", default='project')
    project_id = fields.Many2one('project.project',
                                 string='Project',
                                 help="This indicates the Project")
    task_id = fields.Many2one('project.task',
                              string='Task', help="This indicates the Task")

    @api.model_create_multi
    def create(self, vals_list):
        """Supering the create function inorder to add the project and task
         corresponding to the attachment"""
        for vals in vals_list:
            if 'project_id' in vals.keys() and not vals['task_id']:
                vals['res_id'] = vals['project_id']
                vals['res_model'] = 'project.project'
            elif 'project_id' in vals.keys() and vals['task_id']:
                vals['res_id'] = vals['task_id']
                vals['res_model'] = 'project.task'
            elif ('project_id' not in vals.keys() and vals['res_model'] ==
                  'project.project'):
                vals['project_id'] = vals['res_id']
                vals['attach_to'] = 'project'
            else:
                vals['task_id'] = vals['res_id']
                vals['attach_to'] = 'task'
        return super().create(vals_list)
