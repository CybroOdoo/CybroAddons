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
from odoo import api, fields, models


class ResPartners(models.Model):
    """ Inherit res partner add fields """
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string='Is A Customer',
                                 help='If user is a customer, enable this '
                                      'option')
    is_adult_member = fields.Boolean(string='Is Adult Member?',
                                     help='If user is a adult member, enable '
                                          'this option')
    social_security_no = fields.Integer(string='Social Security Number',
                                        help='To add social security number')
    medicare_no = fields.Integer(string='Medicare Number',
                                 help='To add Medicare number')
    medicaid_no = fields.Integer(string='Medicaid Number',
                                 help='To add Medicaid number')
    birth_date = fields.Date(string='Birth Date', help='To add date of birth')
    age = fields.Integer(string='Age', help='To add age of person')
    referred_by_id = fields.Many2one('res.partner',
                                     string='Referred By',
                                     help='To add referred details')
    marital_status = fields.Selection(
        [('Single', 'Single'), ('Married', 'Married'),
         ('Separated', 'Separated'), ('Widowed', 'Widowed'),
         ('Divorced', 'Divorced')], string='Marital Status',
        help='To add marital details of the person')
    place_birth = fields.Char(string='Birth Place',
                              help='To add place of birth')
    responsible_id = fields.Many2one('hr.employee',
                                     string='Responsible Party/Guardian',
                                     help='To add responsible party/guardian')
    responsible_address = fields.Text(string='Address',
                                      help='To add responsible address')
    responsible_telephone = fields.Char(string='Telephone',
                                        help='To add responsible '
                                             'telephone number')
    care_provider_id = fields.Many2one('hr.employee',
                                       string='Primary Care Provider',
                                       help='To add primary care '
                                            'provider details')
    care_provider_address = fields.Text(string='Address',
                                        help='To add address of care provider')
    care_provider_telephone = fields.Text(string='Telephone',
                                          help='To add care provider '
                                               'telephone number')
    physician = fields.Char(string='Physician', help='To add physician details')
    physician_address = fields.Text(string='Address',
                                    help='To add address of physician')
    physician_phone = fields.Char(string='Phone',
                                  help='To add phone number of physician')
    travel_by = fields.Selection([('Car', 'Car'), ('Bus', 'Bus')],
                                 string='Travel By', help='To add '
                                                          'travel by details')
    travel_assistance = fields.Boolean(string='Is Need Travel Assistance',
                                       help='To add travel assistance details')
    present_medical = fields.Char(string='Present Diagnoses/Medical Problems',
                                  help='To add Present '
                                       'diagnoses/medical problems'
                                  )
    other_disability = fields.Char(string='Other Disability',
                                   help='To add other disabilities')
    weight = fields.Float(string='Weight', help='To add  weight')
    height = fields.Float(string='Height', help='To add  height')
    dentist = fields.Char(string='Dentist Name', help='To add name of dentist')
    dentist_address = fields.Text(string='Address', help='To add '
                                                         'address of dentist')
    dentist_phone = fields.Char(string='Phone', help='To add '
                                                     'phone number of dentist')
    dentist_last_visit = fields.Date(string='Dentist Last Visit',
                                     help="To add dentist's last visit date")
    daycare_activities_ids = fields.One2many('daycare.activities',
                                             'res_partner_id',
                                             string='Daycare Activities',
                                             help='To add daycare '
                                                  'activity details')
    transportation = fields.Selection(
        [('Relative or Friend', 'Relative or Friend'),
         ('Public Transportation', 'Public Transportation'),
         ('Blessed Assurance', 'Blessed Assurance')],
        string='Transportation', help='To add transportation details')
    arrival_time = fields.Float(string='Arrival TIme', help='To add '
                                                            'time of arrival')
    departure_time = fields.Float(string='Departure Time',
                                  help='To add time of departure')
    special_diet = fields.Selection([('Yes', 'Yes'), ('No', 'No')],
                                    string='Special Diet',
                                    help='To add special diet details')
    diet_detail = fields.Char(string='Diet Detail', help='To add details of '
                                                         'diet of the person')
    allergies = fields.Char(string='List of Allergies',
                            help='To add allergies of the person')
    time_request = fields.Char(string='Time Request',
                               help='To add time request details')
    emergency_name = fields.Char(string='Emergency Name',
                                 help='To add emergency contact name')
    applicant_relationship = fields.Char(string='Applicant Relationship',
                                         help='To add relationship with'
                                              ' Applicant')
    emergency_address = fields.Text(string='Emergency address',
                                    help='To add address of emergency contact')
    emergency_phone = fields.Char(string='Emergency phone',
                                  help='To add phone number of '
                                       'emergency Contact')
    first_emergency_name = fields.Char(string='Emergency Name#1',
                                       help='To add name of emergency #1')
    second_applicant_relationship = fields.Char(
        string='Applicant Relationship#2',
        help='To add applicant relationship with #2')
    first_emergency_address = fields.Text(string='Emergency Address#1',
                                          help='To add emergency address of #1')
    first_emergency_phone = fields.Char(string='Emergency Phone#1',
                                        help='To add emergency '
                                             'phone number of #1')
    responsible = fields.Char(string='Responsible', help='To add '
                                                         'responsible Details')
    paid_by = fields.Selection([('Myself', 'Myself'),
                                ('Relative', 'Relative'),
                                ('Another Party', 'Another Party')],
                               string='Paid By', help='To add paid by details')
    paid_by_name = fields.Char(string='Payer Name', help='To add name of payer')
    paid_by_phone = fields.Char(string='Payer Phone',
                                help='To add phone number of payer')
    your_email = fields.Char(string='Email', help='To add email')
    hospital_name = fields.Char(string='Hospital Name', help='To add '
                                                             'name of hospital')
    today_date = fields.Date(string='Today Date', help='To add today date')
    interest_program = fields.Char(string='Interest In Program',
                                   help='To add reason of interest in program')
    previous_experience = fields.Selection([('Yes', 'Yes'),
                                            ('No', 'No')],
                                           string='Previous Experience',
                                           help='To add have previous'
                                                ' experience with program ')
    where_when = fields.Char(string='Where and When',
                             help='To add where and when you have '
                                  'previous experience')
    present_living = fields.Selection([
        ('With Relative', 'With Relative'),
        ('With Non-Relative', 'With Non-Relative'),
        ('Alone(Home/Apartment)', 'Alone(Home/Apartment)'),
        ('Alone(Single Room)', 'Alone(Single Room)')],
        string='Present Living Arrangement',
        help='To add present Living arrangement')
    living_with_whom = fields.Char(string='Living With Whom',
                                   help='To add person living with whom')
    living_with = fields.Char(string='Living With', help='To add '
                                                         'person living with')
    relationship_responsible_relative = fields.Char(
        string='Relationship Responsible Relative',
        help='To add relationship responsible relative details')
    nearest_relative = fields.Char(string='Nearest Relative',
                                   help='To add nearest relative of the person')
    nearest_relative_relation = fields.Char(string='Nearest Relative Relation',
                                            help='To add nearest '
                                                 'relative relation details')
    business_phone = fields.Char(string='Business Phone',
                                 help='To add business phone number')
    employed_at = fields.Char(string='Employed At',
                              help='To add where you employed at')

    @api.onchange('is_adult_member')
    def _onchange_is_adult_member(self):
        """
            When is_adult_member is True, is_customer becomes True and if
            is_adult_member is False then, is_customer becomes False
        """
        self.is_customer = self.is_adult_member
