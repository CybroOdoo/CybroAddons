# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
import requests
from odoo import fields, models
from odoo.exceptions import UserError, ValidationError

MONDAY_API_URL = "https://api.monday.com/v2"
MONDAY_API_VERSION = "2025-07"


class MondayCredential(models.Model):
    """Class containing Monday Credentials which is used to connect
    with Monday.com"""
    _name = "monday.credential"
    _description = "Monday Credentials"

    name = fields.Char(help="Account name", required=True)
    token = fields.Char(help="Token for connecting with Monday.com",
                        groups="base.group_system")

    def _monday_request(self, query, variables=None):
        """Send a GraphQL request to Monday.com and return its ``data``.

        This is the single place where the request is sent and where HTTP,
        JSON and API errors are converted to user-friendly exceptions.

        :param str query: the GraphQL query
        :param dict variables: the variables of the query
        :return: the ``data`` dictionary of the response
        :rtype: dict
        """
        self.ensure_one()
        if not self.token:
            raise UserError(self.env._(
                "Please provide an API Token before connecting to "
                "Monday.com."))
        headers = {
            "Authorization": self.token,
            "API-Version": MONDAY_API_VERSION,
        }
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        try:
            response = requests.post(url=MONDAY_API_URL, json=payload,
                                     headers=headers, timeout=30)
        except requests.exceptions.RequestException as error:
            raise UserError(self.env._(
                "Failed to connect to Monday.com: %(error)s",
                error=error)) from error
        try:
            result = response.json()
        except ValueError:
            result = None
        if not isinstance(result, dict):
            raise UserError(self.env._(
                "Invalid response received from Monday.com "
                "(Status: %(status)s).", status=response.status_code))
        if result.get('error_code'):
            raise ValidationError(result.get(
                'error_message', self.env._("Authentication failed.")))
        if result.get('errors'):
            errors = result['errors']
            if isinstance(errors, list) and errors:
                first = errors[0]
                error_msg = first.get('message', str(first)) \
                    if isinstance(first, dict) else str(first)
            elif isinstance(errors, dict):
                error_msg = errors.get('message', str(errors))
            else:
                error_msg = str(errors)
            raise ValidationError(self.env._(
                "Monday.com API Error: %(error)s", error=error_msg))
        if not response.ok:
            raise UserError(self.env._(
                "Monday.com returned an unexpected status: %(status)s.",
                status=response.status_code))
        return result.get('data') or {}

    def action_test_connection(self):
        """Test the connection to Monday.com using the provided API token."""
        self.ensure_one()
        data = self._monday_request('query { me { id name email } }')
        me = data.get('me') or {}
        user_name = me.get('name', '')
        user_email = me.get('email', '')
        if user_name:
            msg = self.env._(
                "Connection successful! Connected as %(name)s (%(email)s).",
                name=user_name, email=user_email)
        else:
            msg = self.env._(
                "Connection successful! Authenticated with Monday.com.")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Connection Successful'),
                'message': msg,
                'type': 'success',
                'sticky': False,
            }
        }
