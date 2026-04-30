# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class Website(models.Model):
    """  Inherit Website and Adding the necessary fields for Website
    contact us"""
    _inherit = 'website'

    is_company = fields.Boolean("Company Name", help='If it is true it will'
                                                  'show company name on website')
    is_address = fields.Boolean("Address", help='If it is true it will '
                                             'show address on website')
    is_phone = fields.Boolean("Phone", help='If it is true it will show'
                                         ' phone number on website')
    is_email = fields.Boolean("Email", help='If it is true it will show email '
                                         'on website')
    is_website = fields.Boolean("Website", help='If it is true it will show '
                                             'website name on website')
    is_vat = fields.Boolean("VAT", help='If it is true it will show tax id '
                                     'on website')
    is_address_in_online = fields.Boolean("Address in one line", help='If it is'
                            'true it will show address in one line on website')
    is_hide_marker_icons = fields.Boolean("Hide Marker Icons",
                                       help='If it is true it will hide all '
                                            'icons of address on website')
    is_show_phone_icon = fields.Boolean("Show Phone Icons",
                                     help='If it is true it will show only'
                                          ' phone icons on website')
    is_country_flag = fields.Boolean("Country Flag",
                                  help='If it is true it will show country flag'
                                       ' on website')
    is_facebook = fields.Boolean("Facebook", help='If it is true it will show '
                                               'company name on website')
    social_facebook = fields.Char(related='company_id.social_facebook',
                                  readonly=False)
    is_twitter = fields.Boolean("Twitter", help='If it is true it will'
                                             'show twitter on website')
    social_twitter = fields.Char(related='company_id.social_twitter',
                                 readonly=False, help='Twitter account')
    is_linked_in = fields.Boolean("LinkedIn", help='If it is true it will'
                                                'show linkdin on website')
    social_linked_in = fields.Char(related='company_id.social_linkedin',
                                   readonly=False, help='Linkedin account')
    is_instagram = fields.Boolean("Instagram", help='If it is true it will '
                                                 'show instagram on website')
    social_instagram = fields.Char(related='company_id.social_instagram',
                                   readonly=False, help='Instagram account')
    is_git_hub = fields.Boolean("GitHub", help='If it is true it will '
                                            'show github on website',
                             default=False)
    social_git_hub = fields.Char(related='company_id.social_github',
                                 readonly=False, help='Github Account')
