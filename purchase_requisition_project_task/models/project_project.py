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
from odoo import fields, models


class ProjectProject(models.Model):
    """Inheriting model project.project"""
    _inherit = 'project.project'

    purchase_count = fields.Integer(string='Purchase',
                                    compute='_compute_purchase_count',
                                    help='It shows the count of the purchase '
                                          'requisitions that we made for the '
                                          'task in smart tab')

    def action_purchase_requisition(self):
        """ Function that helps to open the purchase agreement open view for
        creating related purchase agreement. If already created it opens the
        tree view of purchase agreement."""
        purchase_requisition = self.env['purchase.requisition']. \
            search([('project_id', '=', self.id)])
        if not purchase_requisition:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Requisition',
                'view_mode': 'form',
                'res_model': 'purchase.requisition',
                'context': {
                    'default_project_id': self.id,
                    'default_is_project': True
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Requisition',
            'view_mode': 'tree,form',
            'res_model': 'purchase.requisition',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'default_is_project': True
            }
        }

    def _compute_purchase_count(self):
        """Function that helps to count the number of purchase agreement
        related with a project"""
        for record in self:
            record.purchase_count = record.env['purchase.requisition']. \
                search_count([('project_id', '=', record.id)])
