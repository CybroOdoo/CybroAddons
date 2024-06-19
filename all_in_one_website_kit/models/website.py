# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class Website(models.Model):
    """ inherit Website adding fields """
    _inherit = 'website'

    mobile_number = fields.Char(string='Mobile Number',
                                help="Defines the mobile number")
    company = fields.Boolean(string="Company Name", default=False,
                             help='If it is true it will show company name on '
                                  'website')
    address = fields.Boolean(string="Address", default=False,
                             help='If it is true it will show address on '
                                  'website')
    phone = fields.Boolean(string="Phone", default=False,
                           help='If it is true it will show phone number on '
                                'website')
    mobile = fields.Boolean(string="Mobile",
                            help='If it is true it will show mobile '
                                 'number on website', default=False)
    email = fields.Boolean(string="Email", default=False,
                           help='If it is true it will show email '
                                'on website')
    website = fields.Boolean(string="Website", default=False,
                             help='If it is true it will show '
                                  'website name on website')
    vat = fields.Boolean(string="VAT", help='If it is true it will show tax id '
                                            'on website', default=False)
    address_in_online = fields.Boolean(string="Address in one line",
                                       help='If it is true it will show address'
                                            ' in one line on website',
                                       default=False)
    hide_marker_icons = fields.Boolean(string="Hide Marker Icons",
                                       help='If it is true it will hide all ico'
                                            'ns of address on website',
                                       default=False)
    show_phone_icon = fields.Boolean(string="Show Phone Icons",
                                     help='If it is true it will show only phon'
                                          'e icons on website',
                                     default=False)
    country_flag = fields.Boolean(string="Country Flag",
                                  help='If it is true it will '
                                       'show country flag on website',
                                  default=False)
    facebook = fields.Boolean(string="Facebook",
                              help='If it is true it will show '
                                   'company name on website',
                              default=False)
    social_facebook = fields.Char(string="Facebook Account",
                                  related='company_id.social_facebook',
                                  readonly=False,
                                  help="Company Facebook Account")
    twitter = fields.Boolean(string="Twitter", help='If it is true it will'
                                                    'show twitter on website',
                             default=False)
    social_twitter = fields.Char(string="Twitter Account",
                                 related='company_id.social_twitter',
                                 readonly=False, help='Twitter account')
    linked_in = fields.Boolean(string="LinkedIn", default=False,
                               help='If it is true it will show twitter '
                                    'on website')
    social_linked_in = fields.Char(string="Linkedin Account",
                                   related='company_id.social_linkedin',
                                   readonly=False, help='Linkedin account')
    instagram = fields.Boolean(string="Instagram", default=False,
                               help='If it is true it will show twitter on '
                                    'website')
    social_instagram = fields.Char(string="Instagram Account",
                                   related='company_id.social_instagram',
                                   readonly=False, help='Instagram account')
    git_hub = fields.Boolean(string="GitHub", default=False,
                             help='If it is true it will show twitter on'
                                  ' website')
    social_git_hub = fields.Char(string="Github Account",
                                 related='company_id.social_github',
                                 readonly=False, help='Github Account')
