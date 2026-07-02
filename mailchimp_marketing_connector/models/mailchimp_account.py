# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class MailchimpAccount(models.Model):
    """This model include fields to connect with mailchimp"""
    _name = 'mailchimp.account'
    _description = 'Mailchimp Account'

    name = fields.Char(string="Name", required=True,
                       help="Name of the Mailchimp account")
    api_key = fields.Char(string="API KEY", required=True,
                          help="Api key for Mailchimp")
    is_auth_success = fields.Boolean(string="is Auth Success",
                                     help="Is Authentication success or not")
    is_auto_sync = fields.Boolean(string="Auto Sync Lists",
                                  help="Automated action for sync lists")

    def connect_mailchimp(self):
        """Function for checking the authentication with mailchimp"""
        try:
            from mailchimp_marketing import Client
            from mailchimp_marketing.api_client import ApiClientError
        except ImportError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Missing Dependency",
                    'message': "Please install the 'mailchimp-marketing' "
                               "Python library: pip install mailchimp-marketing",
                    'type': 'danger',
                    'sticky': True,
                },
            }
        try:
            mailchimp = Client()
            mailchimp.set_config({
                "api_key": self.api_key,
                "server": self.api_key.split('-')[1] if self.api_key else ''
            })
            mailchimp.ping.get()
            self.is_auth_success = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Success",
                    'message': "Authentication successful",
                    'type': 'success',
                    'sticky': False,
                },
            }
        except ApiClientError as error:
            self.is_auth_success = False
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Authentication Failed",
                    'message': error.text,
                    'type': 'danger',
                    'sticky': False,
                },
            }