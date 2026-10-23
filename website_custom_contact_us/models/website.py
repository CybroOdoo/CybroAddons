# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class Website(models.Model):
    """Inherit Website and add fields for Website Contact Us visibility."""

    _inherit = 'website'

    is_company = fields.Boolean(
        string="Company Name",
        default=True,
        help="If checked, shows company name on website.",
    )
    is_address = fields.Boolean(
        string="Address",
        default=True,
        help="If checked, shows address on website.",
    )
    is_phone = fields.Boolean(
        string="Phone",
        default=True,
        help="If checked, shows phone number on website.",
    )
    is_email = fields.Boolean(
        string="Email",
        default=True,
        help="If checked, shows email on website.",
    )
    is_website = fields.Boolean(
        string="Website",
        default=True,
        help="If checked, shows website name on website.",
    )
    is_vat = fields.Boolean(
        string="VAT",
        default=True,
        help="If checked, shows tax ID on website.",
    )
    is_address_in_oneline = fields.Boolean(
        string="Address in One Line",
        default=False,
        help="If checked, shows address in one line on website.",
    )
    is_hide_marker_icons = fields.Boolean(
        string="Hide Marker Icons",
        default=False,
        help="If checked, hides address marker icons on website.",
    )
    is_show_phone_icon = fields.Boolean(
        string="Show Phone Icons",
        default=True,
        help="If checked, shows phone icons on website.",
    )
    is_country_flag = fields.Boolean(
        string="Country Flag",
        default=True,
        help="If checked, shows country flag on website.",
    )
    is_facebook = fields.Boolean(
        string="Facebook",
        default=True,
        help="If checked, shows Facebook on website.",
    )
    social_facebook = fields.Char(
        related='company_id.social_facebook',
        readonly=False,
        string="Facebook Account",
        help="Facebook account URL",
    )
    is_twitter = fields.Boolean(
        string="Twitter",
        default=True,
        help="If checked, shows Twitter on website.",
    )
    social_twitter = fields.Char(
        related='company_id.social_twitter',
        readonly=False,
        string="Twitter Account",
        help="Twitter account URL",
    )
    is_linkedin = fields.Boolean(
        string="LinkedIn",
        default=True,
        help="If checked, shows LinkedIn on website.",
    )
    social_linkedin = fields.Char(
        related='company_id.social_linkedin',
        readonly=False,
        string="LinkedIn Account",
        help="LinkedIn account URL",
    )
    is_instagram = fields.Boolean(
        string="Instagram",
        default=True,
        help="If checked, shows Instagram on website.",
    )
    social_instagram = fields.Char(
        related='company_id.social_instagram',
        readonly=False,
        string="Instagram Account",
        help="Instagram account URL",
    )
    is_github = fields.Boolean(
        string="GitHub",
        default=True,
        help="If checked, shows GitHub on website.",
    )
    social_github = fields.Char(
        related='company_id.social_github',
        readonly=False,
        string="GitHub Account",
        help="GitHub account URL",
    )
