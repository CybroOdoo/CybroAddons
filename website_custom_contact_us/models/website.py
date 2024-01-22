""" Website custom contact Us"""
# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
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


class WebsiteInherited(models.Model):
    """  Inherit Website and Adding the necessary fields for Website
    contact us"""
    _inherit = 'website'

    company = fields.Boolean("Company Name", help='If it is true it will'
                                                  'show company name on website',
                             default=False)
    address = fields.Boolean("Address", help='If it is true it will '
                                             'show address on website',
                             default=False)
    phone = fields.Boolean("Phone", help='If it is true it will show'
                                         ' phone number on website',
                           default=False)
    mobile = fields.Boolean("Mobile", help='If it is true it will show mobile '
                                           'number on website', default=False)
    email = fields.Boolean("Email", help='If it is true it will show email '
                                         'on website', default=False)
    website = fields.Boolean("Website", help='If it is true it will show '
                                             'website name on website',
                             default=False)
    vat = fields.Boolean("VAT", help='If it is true it will show tax id '
                                     'on website', default=False)
    address_in_online = fields.Boolean("Address in one line", help='If it is'
                            'true it will show address in one line on website',
                                       default=False)
    hide_marker_icons = fields.Boolean("Hide Marker Icons", help='If it is true'
                               'it will hide all icons of address on website',
                                       default=False)
    show_phone_icon = fields.Boolean("Show Phone Icons", help='If it is true it'
                                        'will show only phone icons on website',
                                     default=False)
    country_flag = fields.Boolean("Country Flag", help='If it is true it will '
                                                'show country flag on website',
                                  default=False)
    facebook = fields.Boolean("Facebook", help='If it is true it will show '
                                               'company name on website',
                              default=False)
    social_facebook = fields.Char(related='company_id.social_facebook',
                                  readonly=False)
    twitter = fields.Boolean("Twitter", help='If it is true it will'
                                             'show twitter on website',
                             default=False)
    social_twitter = fields.Char(related='company_id.social_twitter',
                                 readonly=False, help='Twitter account')
    linked_in = fields.Boolean("LinkedIn", help='If it is true it will'
                                                'show twitter on website',
                               default=False)
    social_linked_in = fields.Char(related='company_id.social_linkedin',
                                   readonly=False, help='Linkedin account')
    instagram = fields.Boolean("Instagram", help='If it is true it will '
                                                 'show twitter on website',
                               default=False)
    social_instagram = fields.Char(related='company_id.social_instagram',
                                   readonly=False, help='Instagram account')
    git_hub = fields.Boolean("GitHub", help='If it is true it will '
                                            'show twitter on website',
                             default=False)
    social_git_hub = fields.Char(related='company_id.social_github',
                                 readonly=False, help='Github Account')
