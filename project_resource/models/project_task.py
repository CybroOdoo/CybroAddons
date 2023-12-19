# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    """ Inherits project Task to add fields and to show all free resources
        for the project based on the project start and end dates"""
    _inherit = 'project.task'

    task_start_date = fields.Date(string="Start Date", required=True,
                                  help='Start date of the task')
    users_ids = fields.Many2many('res.users',
                                 compute="_compute_users_ids",
                                 help="This field is to store the users"
                                      " based on the calculation")

    @api.onchange('task_start_date', 'date_deadline')
    def _compute_users_ids(self):
        """ Returning the domain for selecting the free resource """
        if self.date_deadline and self.task_start_date:
            from_date = self.date_deadline
            end_date = self.task_start_date
            resource_ids = self.get_free_resource_ids(from_date, end_date)
            if self.project_id.privacy_visibility == 'followers':
                self.users_ids = self.env['res.users'].search(
                    [('id', 'not in', resource_ids),
                      ('id', 'in', self.project_id.message_follower_ids.ids),
                              ('share', '=', False)])
                self.user_ids.write({'id': [(6, 0, self.users_ids)]})
            else:
                self.users_ids = self.env['res.users'].search([('id', 'not in',
                                                    resource_ids),
                              ('share', '=', False)])
                self.user_ids.write({'id': [(6, 0, self.users_ids)]})

    def get_free_resource_ids(self, from_date, end_date):
        """Function to get the resources for the particular period """
        lst = []
        for task in self.env['res.users'].search([]).project_allocated_ids:
            if task.task_start_date and task.date_deadline:
                if task.task_start_date <= from_date <= task.date_deadline:
                    lst.append(task.manager_id.id)
                    for user in task.user_ids:
                        lst.append(user.id)
                if task.task_start_date <= end_date >= task.date_deadline:
                    lst.append(task.manager_id.id)
                    for user in task.user_ids:
                        lst.append(user.id)
        return_list = list(set(lst))
        return return_list
