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
from odoo import api, fields, models, _


class UniversityStudent(models.Model):
    """To keep records of university student details"""
    _name = 'university.student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'res.partner': 'partner_id'}
    _description = 'University student records'

    @api.model
    def create(self, vals):
        """ This method overrides the create method to assign a sequence number
            to the newly created record.
           :param vals (dict): Dictionary containing the field values for the
                                new university student record.
           :returns class: university.student The created university student
                            record.
        """
        vals['admission_no'] = self.env['ir.sequence'].next_by_code(
            'university.student')
        res = super(UniversityStudent, self).create(vals)
        return res

    partner_id = fields.Many2one(
        'res.partner', string='Partner', help="Student Partner",
        required=True, ondelete="cascade")
    middle_name = fields.Char(string='Middle Name',
                              help="Middle Name of the student")
    last_name = fields.Char(string='Last Name', help="Last name of student")
    application_no = fields.Char(string="Application No",
                                 help="Application number of the student")
    date_of_birth = fields.Date(string="Date of Birth", requird=True,
                                help="Date of Birth details")
    guardian_id = fields.Many2one('res.partner', string="Guardian",
                                  help="Student guardian details",
                                  domain=[('is_parent', '=', True)])
    father_name = fields.Char(string="Father", help="Student father details")
    mother_name = fields.Char(string="Mother", help="Student mother details")
    semester_id = fields.Many2one('university.semester',
                                  string="Semester",
                                  help="Which semester of student is")
    department_id = fields.Many2one(related='semester_id.department_id',
                                    help="Which department in semester",
                                    string="Department")
    course_id = fields.Many2one(related='department_id.course_id',
                                help="Which course in the department",
                                string="Course")
    admission_no = fields.Char(string="Admission Number", readonly=True,
                               help="Admission no. of the student ")
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'),
                               ('other', 'Other')],
                              help="Student gender details",
                              string='Gender', required=True, default='male',
                              track_visibility='onchange')
    blood_group = fields.Selection([('a+', 'A+'),
                                    ('a-', 'A-'),
                                    ('b+', 'B+'),
                                    ('o+', 'O+'),
                                    ('o-', 'O-'),
                                    ('ab-', 'AB-'),
                                    ('ab+', 'AB+')],
                                   string='Blood Group', required=True,
                                   help="Student blood group details",
                                   default='a+',
                                   track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Company")
    per_street = fields.Char(string="Street", help="Street Address")
    per_street2 = fields.Char(string="Street2", help="Street2 address")
    per_zip = fields.Char(change_default=True, string="Zip",
                          help="Zip/Pincode details")
    per_city = fields.Char(string="City", help="Student living city")
    per_state_id = fields.Many2one("res.country.state",
                                   string='State',help="State",
                                   ondelete='restrict')
    per_country_id = fields.Many2one('res.country',
                                     string='Country',
                                     help="Nationality of student",
                                     ondelete='restrict')
    mother_tongue = fields.Char(string="Mother Tongue",
                                help="Student mother tongue")
    caste = fields.Char(string="Caste",
                               help="Student caste details")
    religion = fields.Char(string="Religion",
                                  help="Student religion details")
    is_same_address = fields.Boolean(string="Is same Address?",
                                     help="Enable if student have single "
                                          "address")
    nationality_id = fields.Many2one('res.country',
                                     string='Nationality',
                                     help="Nationality of student",
                                     ondelete='restrict')
    application_id = fields.Many2one('university.application',
                                     help="Application no of student",
                                     string="Application No")
    user_id = fields.Many2one('res.users', string="User",
                              readonly=True,
                              help="Related User of the student")
    batch_id = fields.Many2one('university.batch', string="Batch",
                               help="Relation to batches of university")
    academic_year_id = fields.Many2one('university.academic.year',
                                       string="Academic Year",
                                       help="Academic year of the student")

    def action_student_documents(self):
        """ Open the documents submitted by the student along with the admission
            application. This method retrieves the documents associated with
            the admission application linked to the current student record.
            :returns dict: A dictionary defining the action to open the
                            'university.document' records.
       """
        self.ensure_one()
        if self.application_id.id:
            documents_list = self.env['university.document'].search(
                [('application_ref_id', '=', self.application_id.id)]).mapped(
                'id')
            return {
                'domain': [('id', 'in', documents_list)],
                'name': _('Documents'),
                'view_mode': 'tree,form',
                'res_model': 'university.document',
                'view_id': False,
                'context': {'application_ref_id': self.application_id.id},
                'type': 'ir.actions.act_window'
            }
