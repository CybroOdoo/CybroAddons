# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import requests
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    """This function is used to add some fields in Configuration setting that
    helps to establish the connection, and also check whether the connection is
     established or not"""
    _inherit = 'res.config.settings'

    is_connect_zendesk = fields.Boolean(string="Connect Zendesk",
                                        help='Do you want to connect with '
                                             'zendesk',
                                        config_parameter= 'odoo_zendesk_connector.is_connect_zendesk')
    company_domain = fields.Char(string='Company Domain',
                                 help="Provide the domain of your company",
                                 config_parameter=
                                 'odoo_zendesk_connector.company_domain')
    company_email = fields.Char(string='Company Email',
                                help='Email of your company',
                                config_parameter=
                                'odoo_zendesk_connector.company_email')
    api_key = fields.Char(string='API', help='Generated api key',
                          config_parameter='odoo_zendesk_connector.api_key')
    password = fields.Char(string='Password', help='Password of Zendesk '
                                                   'account',
                           config_parameter='odoo_zendesk_connector.password')

    def action_test_connection(self):
        """This function is used to check whether the connection is
        established or not"""
        zendesk_email = self.company_email
        zendesk_token = self.api_key
        company_domain = self.company_domain
        zendesk_url = f'https://{company_domain}.zendesk.com/api/v2/'
        endpoint = 'tickets.json'
        headers = {'Content-Type': 'application/json'}
        auth = (zendesk_email + '/token', zendesk_token)
        try:
            response = requests.get(zendesk_url + endpoint, headers=headers,
                                    auth=auth)
            response.raise_for_status()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Connection Test Succeeded!"),
                    'message': _("Everything seems properly set up!"),
                    'sticky': False,
                }
            }
        except requests.exceptions.HTTPError as error:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _(error),
                    'sticky': False,
                }
            }
