# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class PendingTask(models.Model):
    """ Model for Pending Tasks associated with HR Leave Requests."""
    _name = 'pending.task'
    _description = 'Pending Task'

    name = fields.Char(string='Task', required=True,
                       help='Name of the pending task.')
    leave_id = fields.Many2one('hr.leave', string='Leave Request',
                               help="Leave request of the employee.")
    dept_id = fields.Many2one('hr.department', string='Department',
                              related='leave_id.department_id',
                              help="Department of the employee.")
    project_id = fields.Many2one('project.project',
                                 string='Project',required=True,
                                 help="Project of the employee")
    description = fields.Text(string='Description',
                              help="Description of the task.")
    assigned_person_id = fields.Many2one('hr.employee',
                                         string='Assigned to',
                                         help="Employee who is assigned to",
                                         domain="[('department_id', '=', "
                                                "dept_id)]")
    unavailable_employee_ids = fields.Many2many('hr.employee',
                                                string='Unavailable Employees',
                                                help="Name of unavailable"
                                                     "employees",
                                                compute='_compute_unavailable_employee_ids')

    def _compute_unavailable_employee_ids(self):
        """Compute method to determine employees with overlapping leaves."""
        unavailable_employees = []
        for leave in self.leave_id.overlapping_leaves_ids:
            unavailable_employees.append(leave.employee_id.id)
        self.update({'unavailable_employee_ids': unavailable_employees})
