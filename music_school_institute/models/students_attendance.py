# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (<https://www.cybrosys.com>)
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


class StudentsAttendance(models.Model):
    """Model used to create the records of attendance."""
    _name = "students.attendance"
    _description = 'Students Attendance'
    _rec_name = 'student_id'

    student_id = fields.Many2one('res.partner', string='Students',
                                 domain=[('student', '=', True)],
                                 help="Name of the student.", required=True)
    attendance = fields.Selection([('present', 'Present'),
                                   ('absent', 'Absent')], string='Attendance',
                                  help="Attendance selection field.")
    date = fields.Date(string='Date', default=fields.Date.today(),
                       help='Date of the student attendance.')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
