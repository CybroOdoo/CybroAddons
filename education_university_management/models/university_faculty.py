# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class UniversityFaculty(models.Model):
    """For managing faculties of university"""
    _name = 'university.faculty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "University Faculty records"

    name = fields.Char(string='Name', required=True,
                       help="Enter the first name")
    last_name = fields.Char(string='Last Name', help="Enter the last name")
    image = fields.Binary(string="Image", attachment=True,
                          help="Image of the faculty")
    date_of_birth = fields.Date(string="Date of Birth", required=True,
                                help="Enter the DOB")
    email = fields.Char(string="Email", required=True,
                        help="Enter the Email for contact purpose")
    phone = fields.Char(string="Phone",
                        help="Enter the Phone for contact purpose")
    mobile = fields.Char(string="Mobile", required=True,
                         help="Enter the Mobile for contact purpose")
    guardian_id = fields.Char(string="Guardian", help="Your guardian is ")
    father_name = fields.Char(string="Father", help="Your Father name is ")
    mother_name = fields.Char(string="Mother", help="Your Mother name is ")
    degree_id = fields.Many2one('hr.recruitment.degree',
                                string="Degree",
                                Help="Select your Highest degree")
    subject_line_ids = fields.Many2many('university.subject',
                                        string='Subject Lines',
                                        help="Subjects of Faculty")
    employee_id = fields.Many2one('hr.employee',
                                  string="Related Employee",
                                  help="Related employee of faculty")
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        string='Gender', required=True, default='male',
        help="Gender of the faculty",
        track_visibility='onchange')
    blood_group = fields.Selection(
        [('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('o+', 'O+'),
         ('o-', 'O-'), ('ab-', 'AB-'), ('ab+', 'AB+')],
        string='Blood Group', required=True, default='a+',
        help="Blood group of faculty", track_visibility='onchange')

    def action_create_employee(self):
        """Creating the employee for the faculty"""
        for rec in self:
            emp_id = self.env['hr.employee'].create({
                'name': rec.name + ' ' + rec.last_name,
                'gender': rec.gender,
                'birthday': rec.date_of_birth,
                'image_1920': rec.image,
                'work_phone': rec.phone,
                'work_email': rec.email,
            })
            rec.employee_id = emp_id.id
