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
from odoo import models
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """
    Inheriting res.partner to integrate direct SMS sending capabilities.
    Provides action to launch the Send SMS wizard prefilled with the partner's
    phone number.
    """
    _inherit = 'res.partner'

    def send_sms(self):
        """
        Action method to open the Send SMS wizard prefilled with partner
        phone numbers.

        Extracts and normalizes phone numbers for selected partners, locates
        the default SMS gateway configuration, and returns the window action
        to launch the wizard.

        Returns:
            dict: An ir.actions.act_window action dictionary displaying
                  'send.sms' in a modal.
        """
        partner_records = self.browse(
            self.env.context.get('active_ids') or self.ids
        )
        phone_numbers = []
        for partner in partner_records:
            phone_number = partner.phone
            if phone_number:
                phone_number = str(phone_number).strip()
                if not phone_number.startswith('+'):
                    country = partner.country_id or self.env.company.country_id
                    if country and country.phone_code:
                        formatted_number = None
                        try:
                            formatted_number = phone_validation.phone_format(
                                phone_number,
                                country.code,
                                country.phone_code,
                                force_format='E164',
                            )
                        except UserError:
                            formatted_number = None

                        if formatted_number and formatted_number.startswith('+'):
                            phone_number = formatted_number
                        else:
                            clean_digits = ''.join(
                                char for char in phone_number if char.isdigit()
                            )
                            if clean_digits:
                                country_code_str = str(country.phone_code)
                                has_country_prefix = (
                                    clean_digits.startswith(country_code_str)
                                    and len(clean_digits) > len(country_code_str) + 6
                                )
                                if has_country_prefix:
                                    phone_number = f"+{clean_digits}"
                                else:
                                    phone_number = f"+{country_code_str}{clean_digits}"
                phone_numbers.append(phone_number)

        default_gateway_config = self.env['sms.gateway.config'].search([], limit=1)
        return {
            'name': self.env._('Send SMS via Gateway'),
            'type': 'ir.actions.act_window',
            'res_model': 'send.sms',
            'context': {
                'default_recipient_numbers': ','.join(phone_numbers),
                'default_gateway_config_id': (
                    default_gateway_config.id if default_gateway_config else False
                ),
            },
            'view_mode': 'form',
            'target': 'new',
        }
