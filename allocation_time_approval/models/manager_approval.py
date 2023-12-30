# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Farhana Jahan PT(odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class ManagerApproval(models.Model):
    """ Create a new model for obtaining
    Project Time Approval Data for Manager Approval. """
    _name = 'manager.approval'
    _description = "Manager Approval"

    task = fields.Char(string="Task", help="Task name for project")
    project_id = fields.Many2one("project.project", string="Project",
                                 help="Corresponding project name")
    user_ids = fields.Many2many('res.users', string="Assignees",
                                help="Corresponding assignees name",
                                required=True)
    planned_hours = fields.Float(string="Allocated Hours",
                                 help="Allocation time for assignees")
    button_view_boolean = fields.Boolean(string="Button view",
                                         help="Button for approve button")
    button_view_boolean_cancel = fields.Boolean(string="Cancel Button",
                                                help="Button for cancel")
    task_id = fields.Many2one("project.task", string="Project Task",
                              help="Getting corresponding task")

    def action_approve(self):
        """ When click on 'Approve' button the datas are created
         in project_task module"""
        users = [rec for rec in self.user_ids.ids]
        self.task_id.update({
            'name': self.task,
            'project_id': self.project_id.id,
            'user_ids': users,
            'planned_hours': self.planned_hours,
            'stage_id': self.env.ref("project.project_stage_1").id,
            'manager_approval_id': self.id
        })
        self.button_view_boolean = True
        self.button_view_boolean_cancel = False

    def action_manager_cancel(self):
        """When click on 'Cancel' button project.task got cancelled"""
        self.task_id.write({'stage_id': self.env.ref(
            "project.project_stage_3").id})
        self.button_view_boolean_cancel = True
        self.button_view_boolean = False
