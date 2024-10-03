# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
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
##########################################################################
from odoo import models, fields, api


class AdultMembers(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string='Is A Customer',
                                 help='If user is a customer, enable this option')
    is_adult_member = fields.Boolean(string='Is Adult Member?',
                                     help='If user is a adult member, enable this option')
    social_security_no = fields.Integer(string='Social Security Number',
                                        help="User's Social Security Number")
    medicare_no = fields.Integer(string='Medicare Number',
                                 help="User's Medicare Number")
    medicaid_no = fields.Integer(string='Medicaid Number',
                                 help="User's Medicalaid Number")
    birth_date = fields.Date(string='Birth Date', help="Birth Date of User")
    age = fields.Integer(string='Age', help="Age of user")
    referred_by_id = fields.Many2one('res.partner', string='Referred By',
                                     help="Referral of the user")
    marital_status = fields.Selection(
        [('single', 'Single'), ('married', 'Married'),
         ('separated', 'Separated'), ('widowed', 'Widowed'),
         ('divorced', 'Divorced')], string="Marital Status",
        help="Marriage status of the user")
    place_birth = fields.Char(string='Place Of Birth',
                              help="Place of Birth of the user")
    responsible_id = fields.Many2one('hr.employee',
                                     string='Responsible Party/Guardian',
                                     help="Guardian of the user")
    responsible_address = fields.Text(string='Address',
                                      help="Address of the guardian")
    responsible_telephone = fields.Char(string='Telephone',
                                        help="Telephone of the guardian")
    care_provider_id = fields.Many2one('hr.employee',
                                       string='Primary Care Provider',
                                       help="Care provider for the user")
    care_provider_address = fields.Text(string='Address',
                                        help="Address of the care provider")
    care_provider_telephone = fields.Text(string='Telephone',
                                          help="Phone number of the care provider")
    physician_id = fields.Char(string='Physician', help="Physician of the user")
    physician_address = fields.Text(string='Address',
                                    help="Address of the physician")
    physician_phone = fields.Char(string='Phone',
                                  help="Phone number of the physician")
    travel_by = fields.Selection([('car', 'Car'), ('bus', 'Bus')],
                                 string='Travel By',
                                 help="Travel by of the care provider")
    travel_assistance = fields.Boolean(string='Is Need Travel Assistance',
                                       help="Is there any need to travel")
    present_medical = fields.Char(string='Present Diagnoses/Medical Problems',
                                  help='Present medical problems')
    other_disability = fields.Char(string='Other Disability',
                                   help="Any other condition")
    weight = fields.Float(string='Weight', help="Weight of the User")
    height = fields.Float(string='Height', help="Height of the user")
    dentist_id = fields.Char(string='Dentist Name', help="Dentist of the user")
    dentist_address = fields.Text(string='Address',
                                  help="Address of the dentist")
    dentist_phone = fields.Char(string='Phone',
                                help="Phone number of the dentist")
    dentist_last_visit = fields.Date(string='Dentist Last Visit',
                                     help="Lase visit to the dentist")
    daycare_activities_ids = fields.One2many('daycare.activities',
                                             'res_partner_id', string="Daycare",
                                             help="Day care Activities")
    transportation = fields.Selection(
        [('relative_friend', 'Relative or Friend'),
         ('public_transport', 'Public Transportation'),
         ('blessed_assurance', 'Blessed Assurance')],
        string='Transportation', help="Transportation Methods")
    arrival_time = fields.Float(string='Arrival TIme', help="Time of arrival")
    departure_time = fields.Float(string='Departure Time',
                                  help="Time of departure")
    special_diet = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                    string='Special Diet',
                                    help="Any special diet")
    diet_detail = fields.Char(string='Diet Detail',
                              help="If any diet provide in detail")
    allergies = fields.Char(string='List of Allergies', help="Allergies")
    time_request = fields.Char(string='Time Request', help="Requested Time")
    emergency_name = fields.Char(string='Emergency Name',
                                 help="Emergency Contacy")
    applicant_relationship = fields.Char(string='Applicant Relationship',
                                         help="Relation to the user")
    emergency_address = fields.Text(string='Emergency Address',
                                    help="Address of the emergency contact")
    emergency_phone = fields.Char(string='Emergency Phone',
                                  help="Phone number of the emergency contact")
    emergency_name_1 = fields.Char(string='Emergency Name#1',
                                   help="Another emergency contact")
    applicant_relationship_2 = fields.Char(string='Applicant Relationship#2',
                                           help="Relationship to the user")
    emergency_address_1 = fields.Text(string='Emergency Address#1',
                                      help="Address of the emergency contact")
    emergency_phone_1 = fields.Char(string='Emergency Phone#1',
                                    help="Phone number pf the emergency contact2")
    responsible = fields.Char(string='Responsible', help="Responsible person")
    paid_by = fields.Selection([('myself', 'Myself'), ('relative', 'Relative'),
                                ('another_party', 'Another Party')],
                               string='Paid By', help="Payment by")
    paid_by_name = fields.Char(string='Payer Name', help="Name of the Payer")
    paid_by_phone = fields.Char(string='Payer Phone',
                                help="Phone number of the payer")
    your_email = fields.Char(string='Your Email', help="Email of the user")
    hospital_name = fields.Char(string='Hospital Name',
                                help="Name of the hospital")
    today_date = fields.Date(string='Today Date', help="Date of today.")
    interest_program = fields.Char(string='Interest In Program', help="Program "
                                                                      "intrested in")
    previous_experience = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                           string='Previous Experience',
                                           help="Any previous experience")
    where_when = fields.Char(string='Where and When',
                             help="Where and when to select the experience")
    present_living = fields.Selection([('with_relative', 'With Relative'),
                                       ('non_relative', 'With Non-Relative'),
                                       ('home_alone', 'Alone(Home/Apartment)'),
                                       ('alone_single', 'Alone(Single Room)')],
                                      string='Present Living Arrangement',
                                      help="Current Living")
    living_with_whom = fields.Char(string='Living With Whom',
                                   help="Livinig with anyone?")
    living_with = fields.Char(string='Living With', help="Living with Whom")
    relationship_responsible_relative = fields.Char(
        string='Relationship Responsible Relative',
        help="RelationShip with the responsible person")
    nearest_relative = fields.Char(string='Nearest Relative',
                                   help="Nearest Relative")
    nearest_relative_relation = fields.Char(string='Nearest Relative Relation',
                                            help="Relation to the Nearest "
                                                 "Relative")
    business_phone = fields.Char(string='Business Phone',
                                 help="Phone number for business")
    employed_at = fields.Char(string='Employed At', help="Employed")

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
