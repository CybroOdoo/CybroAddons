# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    """ Inherits project Task to add fields and to show all free resources
    for the project based on the project start and end dates"""
    _inherit = 'project.task'

    task_start_date = fields.Date(string="Start Date",
                                  help='Start date of the task')
    users_ids = fields.Many2many('res.users',
                                 compute="_compute_users_ids",
                                 help="This field is to store the users"
                                      " based on the calculation")
    date_deadline = fields.Date(string='Deadline',
                                help='End date of the task')
    manager_id = fields.Many2one('res.users',
                                 string='Project Manager',
                                 related='project_id.user_id',
                                 readonly=True,
                                 help='Project Manager of the task')

    @api.onchange('task_start_date', 'date_deadline')
    def _compute_users_ids(self):
        """ Returning the domain for selecting the free resource """
        for rec in self:
            if rec.date_deadline and rec.task_start_date:
                from_date = rec.date_deadline
                end_date = rec.task_start_date
                resource_ids = rec.get_free_resource_ids(from_date, end_date)
                if rec.project_id.privacy_visibility == 'followers':
                    rec.users_ids = rec.env['res.users'].search(
                        [('id', 'not in', resource_ids),
                         ('id', 'in', rec.project_id.message_follower_ids.ids),
                         ('share', '=', False)])
                    rec.user_ids.write({'id': [(6, 0, rec.users_ids)]})
                else:
                    rec.users_ids = rec.env['res.users'].search([
                        ('id', 'not in', resource_ids),
                        ('share', '=', False)])
                    rec.user_ids.write({'id': [(6, 0, rec.users_ids)]})

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
