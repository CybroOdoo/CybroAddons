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
import logging
from odoo import fields, models
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

_logger = logging.getLogger(__name__)

# Twilio error returned when a trial account may only send predefined texts
TRIAL_TEMPLATE_ERROR = 572006


class TwilioAccount(models.Model):
    """Twilio account holding the credentials and the sender number"""
    _name = 'twilio.account'
    _description = 'Twilio Account'

    name = fields.Char(required=True, help='Name of the Twilio account')
    account_sid = fields.Char(string='Account SID', required=True,
                              groups='base.group_system',
                              help='Account SID for connecting with Twilio')
    auth_token = fields.Char(required=True, groups='base.group_system',
                             help='Auth Token for connecting with Twilio')
    from_number = fields.Char(string='Your Twilio Phone Number',
                              required=True,
                              help='Twilio phone number the SMS are sent '
                                   'from')
    to_number = fields.Char(string='To', required=True,
                            help='Recipient number with country code for '
                                 'testing the connection. It must be added '
                                 'to the Verified Caller IDs in Twilio.')
    body = fields.Text(required=True, help='Body of the test message',
                       default='This message is for testing the Twilio '
                               'connection.')
    state = fields.Selection([
        ('new', 'New'),
        ('confirm', 'Connected'),
    ], default='new', help='State of the Twilio account')

    def _get_client(self):
        """Return a Twilio client for this account."""
        self.ensure_one()
        account = self.sudo()
        return Client((account.account_sid or '').strip(),
                      (account.auth_token or '').strip())

    def _notify(self, message, notification_type, title=None, reload=False):
        """Return a notification action."""
        params = {
            'message': message,
            'type': notification_type,
            'sticky': notification_type != 'success',
        }
        if title:
            params['title'] = title
        if reload:
            params['next'] = {'type': 'ir.actions.client', 'tag': 'reload'}
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': params,
        }

    def action_test_connection(self):
        """Check the credentials and send a test SMS"""
        self.ensure_one()
        try:
            client = self._get_client()
            # Authenticate the Account SID and Auth Token
            client.api.v2010.accounts(self.sudo().account_sid.strip()).fetch()
            try:
                client.messages.create(body=self.body,
                                       from_=self.from_number,
                                       to=self.to_number)
            except TwilioRestException as error:
                # Trial accounts may only send predefined texts, but the
                # credentials are valid
                if str(error.code) != str(TRIAL_TEMPLATE_ERROR) and \
                        'trial accounts' not in str(error).lower():
                    raise
                self.state = 'confirm'
                return self._notify(
                    self.env._("The credentials are valid, but the Twilio "
                               "account is in trial mode, so only "
                               "predefined texts can be sent."),
                    'warning',
                    title=self.env._("Connected (Trial Mode)"),
                    reload=True)
            self.state = 'confirm'
            return self._notify(self.env._("Connection successful."),
                                'success', reload=True)
        except Exception as error:
            _logger.exception("Twilio connection failed: %s", error)
            return self._notify(
                self.env._("Connection failed: %s",
                           getattr(error, 'msg', str(error))),
                'danger')
