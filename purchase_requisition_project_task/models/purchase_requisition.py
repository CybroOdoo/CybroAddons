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
    """Inheriting model purchase requisition"""
    _inherit = 'purchase.requisition'

    project_id = fields.Many2one('project.project', string='Project',
                                 help='It helps to get the project '
                                      'from project module')
    task_ids = fields.Many2many('project.task',
                                help='this filed show all the tasks of the '
                                     'selected project.')

    @api.onchange('project_id')
    def _onchange_project_task(self):
        """ Function that helps to automatically fill the related task field
        when we select a project."""
        if self.project_id:
            self.task_ids = self.env['project.task'].\
                search([('project_id', '=', self.project_id.id)])
