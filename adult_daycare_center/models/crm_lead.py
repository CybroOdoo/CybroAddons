# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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


class CrmLead(models.Model):
    """ Adding fields in crm lead for day care """
    _inherit = 'crm.lead'

    birth_date = fields.Date(string='Birthdate', help='Date of Birth')
    gender = fields.Selection([('Male', 'Male'), ('Female', 'Female')],
                              string='Gender', help='Gender of the person')
    medicaid = fields.Integer(string='Medicaid', help='To add medicaid details')
    medicare = fields.Integer(string='Medicare', help='To add medicare details')
    supplemental_income = fields.Float(string='Supplemental Security Income',
                                       help='To add supplemental security'
                                            ' income details')
    interest_program = fields.Char(string='Interest In Program',
                                   help='To add reason of interest in program')
    previous_experience = fields.Selection([('Yes', 'Yes'),
                                            ('No', 'No')],
                                           string='Previous Experience',
                                           help='Do you have previous program '
                                                'experience')
    where_when = fields.Char(string='Where and When',
                             help='Where and when you have previous'
                                  ' program experience')
    marital_status = fields.Selection(
        [('Single', 'Single'), ('Married', 'Married'),
         ('Separated', 'Separated'), ('Widowed', 'Widowed'),
         ('Divorced', 'Divorced')], string='Marital Status',
        help='To add marital status of person')
    present_living = fields.Selection([
        ('With Relative', 'With Relative'),
        ('With Non-Relative', 'With Non-Relative'),
        ('Home Alone', 'Alone(Home/Apartment)'),
        ('Alone Single', 'Alone(Single Room)')],
        string='Present Living Arrangement',
        help='To add the person present Living Agreement')
    living_with_whom = fields.Char(string='Living With Whom',
                                   help='To add person living with whom')
    living_with = fields.Char(string='Living With',
                              help='To add person living with details')
    relationship_responsible_relative = fields.Char(
        string='Relationship Responsible Relative',
        help='To add details of  relationship responsible relative')
    nearest_relative = fields.Char(string='Nearest Relative',
                                   help='To add nearest relative of the person')
    nearest_relative_relation = fields.Char(string='Nearest Relative Relation',
                                            help='Nearest relative '
                                                 'relation with the person')
    business_phone = fields.Char(string='Business Phone',
                                 help='To add business Phone Number')
    emergency_name = fields.Char(string='Emergency Name', help='To add '
                                                               'emergency Name')
    applicant_relationship = fields.Char(string='Applicant Relationship',
                                         help='To add relationship with'
                                              'applicant')
    emergency_address = fields.Text(string='Emergency Address',
                                    help='To add emergency contact address')
    emergency_phone = fields.Char(string='Emergency Phone',
                                  help='To add emergency Phone Number')
    first_emergency_name = fields.Char(string='Emergency Name#1',
                                       help='To add emergency contact name#1')
    second_applicant_relationship = fields.Char(
        string='Applicant Relationship#2',
        help='To add relationship with applicant#2')
    first_emergency_address = fields.Text(string='Emergency Address#1',
                                          help='To add emergency address of #1')
    first_emergency_phone = fields.Char(string='Emergency Phone#1',
                                        help='To add emergency'
                                             'phone number of #1')
    physician_name = fields.Char(string='Physician Name',
                                 help='To add name of physician')
    physician_address = fields.Text(string='Physician Address',
                                    help='To add address of physician')
    physician_phone = fields.Char(string='Physician Phone',
                                  help='To add phone number of physician')
    physician_last_visit = fields.Date(string='Physician Last Visit',
                                       help='To add last visit date with '
                                            'physician')
    dentist_name = fields.Char(string='Dentist Name', help='To add name of'
                                                           ' dentist')
    dentist_address = fields.Text(string='Dentist Address',
                                  help='To add address of dentist')
    dentist_phone = fields.Char(string='Dentist Phone',
                                help='To add phone number of dentist')
    dentist_last_visit = fields.Date(string='Dentist Last Visit',
                                     help='To add last visit with dentist')
    transportation = fields.Selection(
        [('Relative or Friend', 'Relative or Friend'),
         ('Public Transportation', 'Public Transportation'),
         ('Blessed Assurance', 'Blessed Assurance')],
        string='Transportation', help='To add transportation with')
    arrival_time = fields.Float(string='Arrival TIme', help='To add time of '
                                                            'arrival')
    departure_time = fields.Float(string='Departure Time',
                                  help='To add time of departure')
    special_diet = fields.Selection([('Yes', 'Yes'), ('No', 'No')],
                                    string='Special Diet',
                                    help='To add person have any special Diet?')
    responsible = fields.Char(string='Responsible', help='To add '
                                                         'responsible person')
    paid_by = fields.Selection([('Myself', 'Myself'),
                                ('Relative', 'Relative'),
                                ('Another Party', 'Another Party')],
                               string='Paid By', help='To add paid by details')
    paid_by_name = fields.Char(string='Payer Name', help='To add name of payer')
    paid_by_phone = fields.Char(string='Payer Phone',
                                help='To add phone number of payer')
    your_email = fields.Char(string='Your Email', help='To add your email '
                                                       'address', )
    hospital_name = fields.Char(string='Hospital Name', help='Name of Hospital')
    today_date = fields.Date(string='Today Date', default=fields.Date.today,
                             help="Today's Date")
    diet_detail = fields.Char(string='Diet Detail', help='Details of your Diet')
    allergies = fields.Char(string='List of Allergies',
                            help='To add person allergy details')
    time_request = fields.Char(string='Time Request',
                               help='To add time request of the person')
    employed_at = fields.Char(string='Employed At', help='To add employed at'
                                                         ' details')
    request_assurance = fields.Char(string='Blessed Assurance',
                                    help='To add blessed assurance details')

    def action_updt_adult_info(self):
        """
            This function Updates the daycare data inside res.partner with the
            corresponding data in the crm.lead model
        """
        adult_person = self.env['res.partner'].browse(self.partner_id.id)
        adult_person.update({
            'is_customer': True,
            'is_adult_member': True,
            'medicare_no': self.medicare,
            'medicaid_no': self.medicaid,
            'birth_date': self.birth_date,
            'marital_status': self.marital_status,
            'physician': self.physician_name,
            'physician_address': self.physician_address,
            'physician_phone': self.physician_phone,
            'dentist': self.dentist_name,
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
            'first_emergency_name': self.first_emergency_name,
            'second_applicant_relationship': self.second_applicant_relationship,
            'first_emergency_address': self.first_emergency_address,
            'first_emergency_phone': self.first_emergency_phone,
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
