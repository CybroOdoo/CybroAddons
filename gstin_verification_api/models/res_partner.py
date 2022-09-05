# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, _
from odoo.exceptions import UserError
import requests


class ResPartner(models.Model):
    _description = "Adding the Verify GSTIN button on customer form"
    _inherit = 'res.partner'

    def verify_gstin(self):
        """
        For the Verify GSTIN button that calls the API
        """
        for rec in self:
            if not rec.vat:
                raise UserError("GST Identification Number not assigned")

            # Generating access token
            url = "https://pro.mastersindia.co/oauth/access_token"

            username = self.env['ir.config_parameter'].get_param(
                'autotax_username')
            password = self.env['ir.config_parameter'].get_param(
                'autotax_password')
            client_id = self.env['ir.config_parameter'].get_param(
                'autotax_client_id')
            client_secret = self.env['ir.config_parameter'].get_param(
                'autotax_client_secret')

            params = {
                "username": username,
                "password": password,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "password"
            }
            headers = {
                "Content-type": "application/x-www-form-urlencoded",
            }
            response = requests.post(url, data=params, headers=headers)
            try:
                # GSTIN Verification
                if response.json()['access_token']:
                    token = response.json()['access_token']
                    headers = {
                        "Content-type": "application/json",
                        "Authorization": "Bearer " + token,
                        "client_id": client_id
                    }
                    api_endpoint = "https://commonapi.mastersindia.co/commonapis/searchgstin?gstin=" + rec.vat
                    response = requests.get(api_endpoint, headers=headers)
                    if not response.json()['error']:
                        notification = {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Success'),
                                'type': 'success',
                                'message': 'GSTIN Verified Successfully',
                                'sticky': True,
                            }
                        }
                    else:
                        notification = {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Error'),
                                'type': 'warning',
                                'message': response.json()['message'],
                                'sticky': True,
                            }
                        }
                    return notification
            except KeyError:
                if response.json()['error']:
                    if response.json()['error'] in ['invalid_client',
                                                    'invalid_grant']:
                        raise UserError(
                            "Invalid Autotax Credentials. Please check and try again.")
