# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import models, fields, api


class AdultMembers(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string='Is A Customer',
                                 help='If user is a customer, enable this option')
    is_adult_member = fields.Boolean(string='Is Adult Member?',
                                     help='If user is a adult member, enable this option')
    social_security_no = fields.Integer(string='Social Security Number')
    medicare_no = fields.Integer(string='Medicare Number')
    medicaid_no = fields.Integer(string='Medicaid Number')
    birth_date = fields.Date(string='Birth Date')
    age = fields.Integer(string='Age')
    referred_by_id = fields.Many2one('res.partner', string='Referred By')
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'),
                                       ('separated', 'Separated'), ('widowed', 'Widowed'),
                                       ('divorced', 'Divorced')])
    place_birth = fields.Char(string='Place Of Birth')
    responsible_id = fields.Many2one('hr.employee', string='Responsible Party/Guardian')
    responsible_address = fields.Text(string='Address')
    responsible_telephone = fields.Char(string='Telephone',)
    care_provider_id = fields.Many2one('hr.employee', string='Primary Care Provider')
    care_provider_address = fields.Text(string='Address')
    care_provider_telephone = fields.Text(string='Telephone',)
    physician_id = fields.Char(string='Physician')
    physician_address = fields.Text(string='Address')
    physician_phone = fields.Char(string='Phone')
    travel_by = fields.Selection([('car', 'Car'), ('bus', 'Bus')])
    travel_assistance = fields.Boolean(string='Is Need Travel Assistance')
    present_medical = fields.Char(string='Present Diagnoses/Medical Problems')
    other_disability = fields.Char(string='Other Disability')
    weight = fields.Float(string='Weight')
    height = fields.Float(string='Height')
    dentist_id = fields.Char(string='Dentist Name')
    dentist_address = fields.Text(string='Address')
    dentist_phone = fields.Char(string='Phone')
    dentist_last_visit = fields.Date(string='Dentist Last Visit')
    daycare_activities_ids = fields.One2many('daycare.activities', 'res_partner_id')

    transportation = fields.Selection([('relative_friend', 'Relative or Friend'),
                                       ('public_transport', 'Public Transportation'),
                                       ('blessed_assurance', 'Blessed Assurance')],
                                      string='Transportation')
    arrival_time = fields.Float(string='Arrival TIme')
    departure_time = fields.Float(string='Departure Time')
    special_diet = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Special Diet')
    diet_detail = fields.Char(string='Diet Detail')
    allergies = fields.Char(string='List of Allergies')
    time_request = fields.Char(string='Time Request')
    emergency_name = fields.Char(string='Emergency Name')
    applicant_relationship = fields.Char(string='Applicant Relationship')
    emergency_address = fields.Text(string='Emergency Address')
    emergency_phone = fields.Char(string='Emergency Phone')
    emergency_name_1 = fields.Char(string='Emergency Name#1')
    applicant_relationship_2 = fields.Char(string='Applicant Relationship#2')
    emergency_address_1 = fields.Text(string='Emergency Address#1')
    emergency_phone_1 = fields.Char(string='Emergency Phone#1')

    responsible = fields.Char(string='Responsible')
    paid_by = fields.Selection([('myself', 'Myself'), ('relative', 'Relative'),
                                ('another_party', 'Another Party')], string='Paid By')
    paid_by_name = fields.Char(string='Payer Name')
    paid_by_phone = fields.Char(string='Payer Phone')
    your_email = fields.Char(string='Your Email')
    hospital_name = fields.Char(string='Hospital Name')
    today_date = fields.Date(string='Today Date')

    interest_program = fields.Char(string='Interest In Program')
    previous_experience = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                           string='Previous Experience')
    where_when = fields.Char(string='Where and When')
    present_living = fields.Selection([('with_relative', 'With Relative'),
                                       ('non_relative', 'With Non-Relative'),
                                       ('home_alone', 'Alone(Home/Apartment)'),
                                       ('alone_single', 'Alone(Single Room)')],
                                      string='Present Living Arrangement')
    living_with_whom = fields.Char(string='Living With Whom')
    living_with = fields.Char(string='Living With')
    relationship_responsible_relative = fields.Char(
        string='Relationship Responsible Relative')
    nearest_relative = fields.Char(string='Nearest Relative')
    nearest_relative_relation = fields.Char(string='Nearest Relative Relation')
    business_phone = fields.Char(string='Business Phone')
    employed_at = fields.Char(string='Employed At')

    @api.onchange('is_adult_member')
    def _onchange_is_adult_member(self):
        """
            When is_adult_member is True, is_customer becomes True and if
            is_adult_member is False then, is_customer becomes False
        """
        if self.is_adult_member:
            self.is_customer = True
        else:
            self.is_customer = False
