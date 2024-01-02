# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jibin James (odoo@cybrosys.com)
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
###################################################################################

from datetime import timedelta
from odoo import models, fields, api


class ResourceProject(models.Model):
    """ Task Model"""
    _inherit = 'project.task'

    task_start_date = fields.Date(sting="Start Date", required=True,
                                  help='Task end date')

    @api.onchange('task_start_date', 'date_deadline')
    def select_employee(self):
        """ returning the domain for selcting the free resource"""
        if self.date_deadline and self.task_start_date:
            from_date = self.date_deadline
            end_date = self.task_start_date
            resource_ids = self.get_free_resource_ids(from_date, end_date)
            print(resource_ids,self.project_id.privacy_visibility, "ids")
            if self.project_id.privacy_visibility == 'followers':
                return {'domain':
                        {'user_id':
                            [('id', 'not in', resource_ids),
                             ('id', 'in', self.project_id.allowed_internal_user_ids.ids),
                             ('share', '=', False)]}}
            else:
                return {'domain': {'user_id': [('id', 'not in', resource_ids),
                                               ('share', '=', False)]}}

    def get_free_resource_ids(self, from_date, end_date):
        """getting the resources for the particular period """
        lst = []
        date_lst = []
        date_curent_list = []
        res_pro = self.env['res.users'].search([])
        for rec in res_pro.project_allocated_ids:

            if rec.task_start_date and rec.date_deadline:
                if rec.task_start_date <= from_date <= rec.date_deadline:
                    lst.append(rec.user_id.id)
                if rec.task_start_date <= end_date <= rec.date_deadline:
                    lst.append(rec.user_id.id)

                delta = rec.date_deadline - rec.task_start_date
                for i in range(delta.days + 1):
                    date_lst.append(rec.task_start_date + timedelta(days=i))

                delta = end_date - from_date
                for i in range(delta.days + 1):
                    date_curent_list.append(from_date + timedelta(days=i))

                if from_date not in date_lst and end_date not in date_lst:
                    for rec_date in date_curent_list:
                        if rec_date in date_lst:
                            lst.append(rec.user_id.id)
        return_list = list(set(lst))
        return return_list


class ProjectEmployee(models.Model):
    """To know the assigned/free users"""
    _inherit = 'res.users'

    project_allocated_ids = fields.One2many('project.task',
                                            'user_id',
                                            string='Assigned Task',
                                            help='assigned tasks')
