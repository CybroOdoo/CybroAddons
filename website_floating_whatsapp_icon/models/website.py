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
import re

from odoo import api, fields, models


class Website(models.Model):
    """ Inheriting website model for adding mobile number """
    _inherit = 'website'

    mobile_number = fields.Char(string='Mobile Number',
                                help="Your WhatsApp mobile number")
    sanitized_mobile_number = fields.Char(
        string='Sanitized Mobile Number',
        compute='_compute_sanitized_mobile_number',
        store=True,
        help="Sanitized mobile number containing only numeric digits for WhatsApp"
    )

    @api.depends('mobile_number')
    def _compute_sanitized_mobile_number(self):
        """Compute the sanitized mobile number containing digits only."""
        for website in self:
            if website.mobile_number:
                digits = re.sub(r'\D', '', website.mobile_number)
                website.sanitized_mobile_number = digits or False
            else:
                website.sanitized_mobile_number = False
