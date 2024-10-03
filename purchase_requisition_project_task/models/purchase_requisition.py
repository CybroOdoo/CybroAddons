# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class PurchaseRequisition(models.Model):
    """Added two fields to get the project and its task to connect with the
       project and task."""
    _inherit = 'purchase.requisition'

    def default_project_id(self):
        """Method default_project_id to add the default project as the current
        when created the purchase requisition from the project view"""
        if self._context.get('active_model') == 'project.project':
            project_id = self._context.get('active_id')
            return project_id

    project_id = fields.Many2one('project.project', string='Project',
                                 help='It helps to get the project from '
                                      'project module',
                                 default=default_project_id)
    task_ids = fields.Many2many('project.task', help='this field '
                                                     'show all the '
                                                     'tasks of the selected '
                                                     'project.', string='Task')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """ Function that helps to automatically fill the related task field
        when we select a project."""
        if self.project_id:
            self.task_ids = self.env['project.task']. \
                search([('project_id', '=', self.project_id.id)])
