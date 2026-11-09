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

try:
    from telesign.messaging import MessagingClient
except ImportError:
    MessagingClient = None

try:
    from twilio.rest import Client
except ImportError:
    Client = None

try:
    from vonage import Auth, Vonage
    from vonage_messages import Sms
except ImportError:
    Auth = None
    Vonage = None
    Sms = None

from odoo import fields, models
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError


class SendSms(models.TransientModel):
    """
    Wizard model to compose and send SMS messages across multiple SMS gateways
    including Vonage, Twilio, and TeleSign.
    """
    _name = 'send.sms'
    _description = 'Send SMS Wizard'

    gateway_config_id = fields.Many2one(
        'sms.gateway.config',
        string='SMS Gateway',
        required=True,
        help='Select the SMS gateway configuration to use for sending.'
    )
    recipient_numbers = fields.Char(
        string='Recipients',
        required=True,
        help='Comma-separated recipient mobile phone numbers (e.g., +919876543210).'
    )
    message_text = fields.Text(
        string='Message',
        required=True,
        help='Message text content to be delivered to recipients.'
    )

    def action_send_sms(self):
        """
        Execute SMS sending flow across the configured SMS gateway and record delivery logs.

        Returns:
            dict: Client action dictionary displaying a success notification and closing the wizard.

        Raises:
            UserError: If gateway configuration is missing, no recipients exist,
                       or sending fails on the third-party gateway.
        """
        self.ensure_one()
        if not self.gateway_config_id:
            raise UserError(self.env._('Please select an SMS Gateway configuration.'))
        if not self.recipient_numbers:
            raise UserError(self.env._('Please provide a recipient phone number.'))

        normalized_phone_numbers = self._get_recipient_phone_numbers()
        if not normalized_phone_numbers:
            raise UserError(self.env._('No valid phone numbers found to send SMS.'))

        gateway_name = (self.gateway_config_id.gateway_name or '').lower()

        if gateway_name == 'vonage':
            self._send_via_vonage(normalized_phone_numbers)
        elif gateway_name == 'twilio':
            self._send_via_twilio(normalized_phone_numbers)
        elif gateway_name == 'telesign':
            self._send_via_telesign(normalized_phone_numbers)
        else:
            raise UserError(
                self.env._(
                    "Unsupported SMS Gateway: %(gateway)s",
                    gateway=self.gateway_config_id.gateway_name or 'None',
                )
            )

        self._create_sms_history_records(normalized_phone_numbers)
        self._post_chatter_notification()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('SMS Sent'),
                'message': self.env._('SMS has been sent successfully.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _normalize_phone_number(self, phone_number, country=None):
        """
        Normalize a phone number to standard E.164 format (+[country_code][number]).

        Args:
            phone_number (str): The raw phone number string to normalize.
            country (res.country, optional): Country record used to infer country phone code.

        Returns:
            str or False: Normalized E.164 phone number, or False if invalid.
        """
        if not phone_number or not isinstance(phone_number, str):
            return False
        phone_number = phone_number.strip()
        if not phone_number:
            return False

        country_code = (
            country.code if country and hasattr(country, 'code') and country.code else None
        )
        country_phone_code = (
            country.phone_code
            if country and hasattr(country, 'phone_code') and country.phone_code
            else None
        )

        formatted_number = None
        try:
            region = None if phone_number.startswith('+') else country_code
            formatted_number = phone_validation.phone_format(
                phone_number,
                region,
                country_phone_code,
                force_format='E164',
                raise_exception=False,
            )
        except UserError:
            formatted_number = None

        has_valid_e164 = (
            formatted_number
            and formatted_number.startswith('+')
            and formatted_number != phone_number
        )
        if has_valid_e164:
            clean_e164 = '+' + re.sub(r'\D', '', formatted_number[1:])
            if len(clean_e164) > 1:
                return clean_e164
        elif formatted_number and formatted_number.startswith('+'):
            if re.match(r'^\+\d{7,15}$', formatted_number):
                return formatted_number

        # Fallback normalization when phone_validation tool cannot parse
        clean_digits = re.sub(r'\D', '', phone_number)
        if not clean_digits:
            return False

        if phone_number.startswith('+'):
            return f"+{clean_digits}"

        if country_phone_code:
            country_code_str = str(country_phone_code)
            if clean_digits.startswith('0') and not clean_digits.startswith('00'):
                trunk_stripped = clean_digits.lstrip('0')
                if trunk_stripped:
                    clean_digits = trunk_stripped

            has_country_digits = (
                clean_digits.startswith(country_code_str)
                and len(clean_digits) > len(country_code_str) + 6
            )
            if has_country_digits:
                return f"+{clean_digits}"
            return f"+{country_code_str}{clean_digits}"

        return f"+{clean_digits}"

    def _get_recipient_phone_numbers(self):
        """
        Parse, validate, and normalize recipient phone numbers from the wizard input.

        Returns:
            list[str]: List of valid E.164 normalized recipient phone numbers.
        """
        raw_number_list = [
            num.strip() for num in self.recipient_numbers.split(',') if num.strip()
        ]
        if not raw_number_list:
            return []

        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        country = None
        if active_model == 'res.partner' and active_id and active_model in self.env:
            partner_record = self.env[active_model].browse(active_id)
            country = getattr(partner_record, 'country_id', None)
        if not country:
            country = self.env.company.country_id

        normalized_phone_numbers = []
        for raw_number in raw_number_list:
            normalized_number = self._normalize_phone_number(raw_number, country=country)
            if normalized_number:
                normalized_phone_numbers.append(normalized_number)
            else:
                clean_digits = re.sub(r'[^\d+]', '', raw_number)
                if clean_digits:
                    normalized_phone_numbers.append(clean_digits)

        return normalized_phone_numbers

    def _send_via_vonage(self, recipient_numbers):
        """
        Dispatch SMS messages via the Vonage Messages API.

        Args:
            recipient_numbers (list[str]): List of normalized recipient phone numbers.

        Raises:
            UserError: If client initialization or message sending fails.
        """
        if Vonage is None or Auth is None or Sms is None:
            raise UserError(self.env._("The 'vonage' Python library is not installed."))

        api_key = (self.gateway_config_id.vonage_key or '').strip()
        api_secret = (self.gateway_config_id.vonage_secret or '').strip()
        try:
            vonage_client = Vonage(Auth(
                api_key=api_key,
                api_secret=api_secret,
            ))
        except Exception as error:
            raise UserError(
                self.env._("Vonage configuration error: %(error)s", error=error)
            )

        clean_company = re.sub(r'[^a-zA-Z0-9]', '', self.env.company.name or '')[:11]
        sender = clean_company or 'Vonage'
        for phone_number in recipient_numbers:
            try:
                formatted_number = phone_number.lstrip('+')
                vonage_client.messages.send(
                    Sms(
                        to=formatted_number,
                        from_=sender,
                        text=self.message_text,
                    )
                )
            except UserError:
                raise
            except Exception as error:
                raise UserError(
                    self.env._(
                        "Vonage error for %(number)s: %(error)s",
                        number=phone_number,
                        error=error,
                    )
                )

    def _send_via_twilio(self, recipient_numbers):
        """
        Dispatch SMS messages via the Twilio Messages API.

        Args:
            recipient_numbers (list[str]): List of normalized recipient phone numbers.

        Raises:
            UserError: If client initialization or message transmission encounters an error.
        """
        if Client is None:
            raise UserError(self.env._("The 'twilio' Python library is not installed."))

        account_sid = (self.gateway_config_id.twilio_account_sid or '').strip()
        auth_token = (self.gateway_config_id.twilio_auth_token or '').strip()
        sender_phone_number = str(self.gateway_config_id.twilio_phone_number or '').strip()
        try:
            twilio_client = Client(account_sid, auth_token)
        except Exception as error:
            raise UserError(
                self.env._("Twilio configuration error: %(error)s", error=error)
            )

        for phone_number in recipient_numbers:
            try:
                twilio_client.messages.create(
                    to=phone_number,
                    from_=sender_phone_number,
                    body=self.message_text,
                )
            except UserError:
                raise
            except Exception as error:
                raw_error = getattr(error, 'msg', None) or str(error)
                clean_error = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', raw_error).strip()
                lower_error = clean_error.lower()

                code = getattr(error, 'code', None)
                if code == 572006 or 'predefined sms templates' in lower_error:
                    clean_error = self.env._(
                        "Trial accounts can only use predefined template keywords "
                        "(e.g. 'sms_delivery_updates')."
                    )
                elif (code == 21608 or 'verified recipient' in lower_error
                      or 'unverified' in lower_error):
                    clean_error = self.env._(
                        "Recipient number is not verified in your Twilio trial account."
                    )

                raise UserError(
                    self.env._(
                        "Twilio error for %(number)s: %(error)s",
                        number=phone_number,
                        error=clean_error,
                    )
                )

    def _send_via_telesign(self, recipient_numbers):
        """
        Dispatch SMS messages via the TeleSign Messaging API.

        Args:
            recipient_numbers (list[str]): List of normalized recipient phone numbers.

        Raises:
            UserError: If client initialization fails or TeleSign returns an error status.
        """
        if MessagingClient is None:
            raise UserError(self.env._("The 'telesign' Python library is not installed."))

        customer_id = (self.gateway_config_id.telesign_customer or '').strip()
        api_key = (self.gateway_config_id.telesign_api_key or '').strip()
        try:
            telesign_client = MessagingClient(customer_id, api_key)
        except Exception as error:
            raise UserError(
                self.env._("TeleSign configuration error: %(error)s", error=error)
            )

        for phone_number in recipient_numbers:
            try:
                response = telesign_client.message(phone_number, self.message_text, 'ARN')
            except Exception as error:
                raise UserError(
                    self.env._("TeleSign connection error: %(error)s", error=error)
                )

            json_data = getattr(response, 'json', None)
            status_info = json_data.get('status', {}) if isinstance(json_data, dict) else {}
            status_code = status_info.get('code')
            status_desc = status_info.get('description', '')

            # Status codes 200 (Delivered/Final OK) and 290 (Message in progress) are successful
            if status_code in (200, 290) or (response.ok and not status_code):
                continue

            # Handle TeleSign error responses
            if status_code == 11000 or 'phone_number' in status_desc.lower():
                raise UserError(
                    self.env._(
                        "TeleSign error for %(number)s: Invalid phone number format.",
                        number=phone_number,
                    )
                )

            if status_code == 10033 or 'not been verified' in status_desc.lower():
                raise UserError(
                    self.env._(
                        "TeleSign error for %(number)s: Recipient number is not verified "
                        "in your TeleSign trial account.",
                        number=phone_number,
                    )
                )

            if status_code == 10008 or 'invalid signature' in status_desc.lower():
                raise UserError(
                    self.env._(
                        "TeleSign error for %(number)s: Invalid Signature. Please check "
                        "your Customer ID and API Key in SMS Gateway Configuration.",
                        number=phone_number,
                    )
                )

            err_msg = status_desc or f"HTTP {response.status_code}"
            raise UserError(
                self.env._(
                    "TeleSign error for %(number)s: %(error)s (Status: %(status)s)",
                    number=phone_number,
                    error=err_msg,
                    status=status_code or response.status_code,
                )
            )

    def _create_sms_history_records(self, recipient_numbers):
        """
        Create audit records in sms.history for the sent SMS messages.

        Args:
            recipient_numbers (list[str]): List of recipient phone numbers.
        """
        self.env['sms.history'].sudo().create({
            'sms_gateway_id': self.gateway_config_id.sms_gateway_id.id,
            'sms_mobile': ', '.join(recipient_numbers),
            'sms_text': self.message_text,
            'company_id': self.env.company.id,
        })

    def _post_chatter_notification(self):
        """
        Post notification in active record chatter if wizard was launched from a document.
        """
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        active_ids = self.env.context.get('active_ids') or ([active_id] if active_id else [])
        if active_model and active_ids and active_model in self.env:
            records = self.env[active_model].browse(active_ids)
            for record in records:
                if hasattr(record, 'message_post'):
                    record.message_post(
                        body=self.env._("SMS Sent: %(text)s", text=self.message_text),
                        message_type="comment",
                        subtype_xmlid="mail.mt_comment",
                    )
