# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
# ######################################################################
from odoo import fields, models


class DaycareRequests(models.Model):
    """Extend CRM leads with daycare request and applicant information."""
    _inherit = 'crm.lead'

    birth_date = fields.Date(string='Birthdate', help='Birth date')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                              help="Gender (male or female)")
    medicaid = fields.Integer(help='Medicaid identifier')
    medicare = fields.Integer(help='Medicare identifier')
    supplemental_income = fields.Float(string='Supplemental Security Income',
                                       help="Supplemental security income")
    interest_program = fields.Char(string='Interest In Program',
                                   help="Program the person is interested in")
    previous_experience = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                           help="Whether the person has previous experience")
    where_when = fields.Char(string='Where and When',
                             help="Place and time of the previous experience")
    marital_status = fields.Selection(
        [('single', 'Single'), ('married', 'Married'),
         ('separated', 'Separated'), ('widowed', 'Widowed'),
         ('divorced', 'Divorced')], string='Status', help="Marital status")
    present_living = fields.Selection([('with_relative', 'With Relative'),
                                       ('non_relative', 'With Non-Relative'),
                                       ('home_alone', 'Alone(Home/Apartment)'),
                                       ('alone_single', 'Alone(Single Room)')],
                                      string='Present Living Arrangement',
                                      help="Current Living")
    living_with_whom = fields.Char(help="Living With Whom")
    living_with = fields.Char(help="Living With")
    relationship_responsible_relative = fields.Char(
        help="Responsible Relative of Relationship")
    nearest_relative = fields.Char(help="Nearest Relative of Relationship")
    nearest_relative_relation = fields.Char(help="Relation for nearest Relative")
    business_phone = fields.Char(help="Phone for Business")
    emergency_name = fields.Char(help="Name for emergency")
    applicant_relationship = fields.Char(help="Relationship for applicant")
    emergency_address = fields.Text(help="Address for Emergency")
    emergency_phone = fields.Char(help="Phone for Emergency")
    emergency_name_1 = fields.Char(string='Emergency Name#1',
                                   help="Name for emergency")
    applicant_relationship_2 = fields.Char(string='Applicant Relationship#2',
                                           help="Relationship for application")
    emergency_address_1 = fields.Text(string='Emergency Address#1',
                                      help="Address")
    emergency_phone_1 = fields.Char(string='Emergency Phone#1', help="Phone")
    physician_name = fields.Char(help="Name of the Physician")
    physician_address = fields.Text(help="Address of the Physician")
    physician_phone = fields.Char(help="Phone of the Physician")
    physician_last_visit = fields.Date(help="Last Date that visit the physician")
    dentist_name = fields.Char(help="Name of the dentist")
    dentist_address = fields.Text(help="Address of the dentist")
    dentist_phone = fields.Char(help="Phone number of the dentist")
    dentist_last_visit = fields.Date(help="Last Date that visit the dentist")
    transportation = fields.Selection(
        [('relative_friend', 'Relative or Friend'),
         ('public_transport', 'Public Transportation'),
         ('blessed_assurance', 'Blessed Assurance')],
        help="Transportation")
    arrival_time = fields.Float(help="Time of Arrival")
    departure_time = fields.Float(help="Time of Departure")
    special_diet = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                    help="Special diets")
    responsible = fields.Char(help="Responsible Person")
    paid_by = fields.Selection([('myself', 'Myself'), ('relative', 'Relative'),
                                ('another_party', 'Another Party')],
                               help="Payment by")
    paid_by_name = fields.Char(string='Payer Name', help="Name of the payer")
    paid_by_phone = fields.Char(string='Payer Phone',
                                help="Phone number of the payer")
    your_email = fields.Char(help="Email id")
    hospital_name = fields.Char(help="Name of the hospital")
    today_date = fields.Date(default=fields.Date.today,
                             help="Date of today")
    diet_detail = fields.Char(help="Detail of the Diet")
    allergies = fields.Char(string='List of Allergies', help="All Allergies")
    time_request = fields.Char(help="Requested Time")
    employed_at = fields.Char(help="Employed")
    request_assurance = fields.Char(string='Blessed Assurance',
                                    help="Assurance")

    def action_updt_adult_info(self):
        """
            This function Updates the daycare data inside res.partner with the
            corresponding data in the crm.lead model
        """
        self.ensure_one()
        self.partner_id.write({
            'is_customer': True,
            'is_adult_member': True,
            'medicare_no': self.medicare,
            'medicaid_no': self.medicaid,
            'birth_date': self.birth_date,
            'marital_status': self.marital_status,
            'physician_name': self.physician_name,
            'physician_address': self.physician_address,
            'physician_phone': self.physician_phone,
            'dentist_name': self.dentist_name,
            'dentist_address': self.dentist_address,
            'dentist_phone': self.dentist_phone,
            'dentist_last_visit': self.dentist_last_visit,
            'transportation': self.transportation,
            'arrival_time': self.arrival_time,
            'departure_time': self.departure_time,
            'special_diet': self.special_diet,
            'diet_detail': self.diet_detail,
            'allergies': self.allergies,
            'time_request': self.time_request,
            'emergency_name': self.emergency_name,
            'applicant_relationship': self.applicant_relationship,
            'emergency_address': self.emergency_address,
            'emergency_phone': self.emergency_phone,
            'emergency_name_1': self.emergency_name_1,
            'applicant_relationship_2': self.applicant_relationship_2,
            'emergency_address_1': self.emergency_address_1,
            'emergency_phone_1': self.emergency_phone_1,
            'responsible': self.responsible,
            'paid_by': self.paid_by,
            'paid_by_name': self.paid_by_name,
            'paid_by_phone': self.paid_by_phone,
            'your_email': self.your_email,
            'hospital_name': self.hospital_name,
            'today_date': self.today_date,
            'interest_program': self.interest_program,
            'previous_experience': self.previous_experience,
            'where_when': self.where_when,
            'present_living': self.present_living,
            'living_with_whom': self.living_with_whom,
            'living_with': self.living_with,
            'relationship_responsible_relative': self.relationship_responsible_relative,
            'nearest_relative': self.nearest_relative,
            'nearest_relative_relation': self.nearest_relative_relation,
            'business_phone': self.business_phone,
            'employed_at': self.employed_at,
        })
