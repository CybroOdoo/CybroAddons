# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amal Varghese, Jumana Jabin MP (odoo@cybrosys.com)
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


class SignupConfiguration(models.Model):
    """Model for Signup Configuration.This class represents the Signup
    Configuration model for the Odoo website.It is used to configure the
    signup page, including defining fields, content,and other settings."""
    _name = 'signup.configuration'
    _description = 'Signup Configuration'
    _sql_constraints = [('website_id', 'unique(website_id)',
                         'A record for this website is already exist')]

    name = fields.Char(string='Name', copy=False, required=True,
                       help='The name of the signup configuration.')
    website_id = fields.Many2one(comodel_name='website',
                                 string='Website', required=True,
                                 help='The website associated with the signup'
                                      ' configuration.')
    is_active = fields.Boolean(string='Active', default=True,
                               help='Specifies if the signup configuration is '
                                    'active or not.')
    signup_field_ids = fields.One2many(comodel_name='signup.field',
                                       inverse_name='configuration_id',
                                       string='Signup Fields',
                                       help='The fields associated with the '
                                            'signup configuration.')
    signup_page_content = fields.Html(string='Signup Page Content',
                                      help='The content of the signup page.')
    login_page_content = fields.Html(string='Login Page Content',
                                     help='The content of the login page.')
    reset_password_content = fields.Html(string='Reset Password Content',
                                         help='The content of the reset'
                                              ' password page.')
    background_image = fields.Binary(string='Background Image',
                                     help='The background image for the '
                                          'signup page.')
    is_hide_footer = fields.Boolean(string='Hide Footer from Signup Page',
                                    help='Specifies if the footer should be'
                                         ' hidden on the signup page.')
    is_show_terms_conditions = fields.Boolean(
        string='Show Terms and Condition in Signup Page',
        help='Specifies if the terms and conditions '
             'should be shown on the signup page.')
    terms_and_conditions = fields.Html(string='Terms and Conditions',
                                       help='The terms and conditions'
                                            ' text for the signup page.')
