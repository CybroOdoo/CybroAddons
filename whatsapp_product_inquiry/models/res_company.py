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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """Add the WhatsApp number and message used for product inquiries."""
    _inherit = 'res.company'

    whatsapp_number = fields.Char(
        string="WhatsApp Number",
        help="The company WhatsApp number receiving the inquiry messages, "
             "with the country code and without spaces or signs")
    message = fields.Text(
        default="I want to know more details of the product",
        help="This will be the Inquiry message")

    @api.constrains('whatsapp_number')
    def _check_whatsapp_number(self):
        """The number must only contain digits, as wa.me links require."""
        for company in self:
            number = company.whatsapp_number
            if number and (not number.isdigit() or len(number) <= 8):
                raise ValidationError(self.env._(
                    'The WhatsApp number must be a valid number without '
                    'spaces or signs.'))
