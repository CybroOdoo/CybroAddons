# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """Add a integer field to get the related purchase requisition count"""
    _inherit = 'project.task'

    purchase_count = fields.Integer(string='Purchase',
                                    compute='_compute_purchase_count',
                                    help='It shows the count of the purchase '
                                         'requisitions that we made for the '
                                         'project in smart tab')

    def action_purchase_requisition(self):
        """ function that helps to open the tree view of purchase agreement
        that related with the task"""
        for rec in self:
            new = self.env['purchase.requisition'].search([('task_ids', '=',
                                                            rec.id)])
            if not new:
                raise ValidationError(_("No Purchase Requisition"))
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Requisition',
                'view_mode': 'tree,form',
                'res_model': 'purchase.requisition',
                'domain': [('task_ids', '=', rec.id)]
            }

    def _compute_purchase_count(self):
        """Function that helps to count the number of purchase agreements
        that related with the task."""
        for record in self:
            record.purchase_count = self.env['purchase.requisition']. \
                search_count([('task_ids', '=', record.id)])
