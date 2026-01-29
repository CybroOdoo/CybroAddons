# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-September Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: SREERAG E (<https://www.cybrosys.com>)
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
import re
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
import requests


class PanWiz(models.TransientModel):
    _name = 'pan.api.wizard'
    _order = 'sl_no'

    get_pan = fields.Boolean()
    pan_id = fields.Char(string='PAN Number', required=True)

    @api.onchange('get_pan')
    def get_pan_partner(self):
        self.ensure_one()
        res_partner_id = self.env['res.partner'].search(
            [('id', '=', self.env.context.get('active_id'))])
        if res_partner_id.pan:
            self.pan_id = res_partner_id.pan
            self.get_pan = True

    @api.onchange('pan_id')
    def validate_pan(self):
        val = str(self.pan_id)
        self.pan_id = val.upper()
        regex = "[A-Z]{5}[0-9]{4}[A-Z]{1}"
        pattern = re.compile(regex)
        if not ((re.search(pattern, self.pan_id) and
                 len(self.pan_id) == 10)):
            raise ValidationError("Invalid PAN format !")

    def action_check(self):
        customer_ids = self.env['res.partner'].search(
            [('id', '=', self.env.context.get('active_id'))])
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
                api_endpoint = "https://commonapi.mastersindia.co/commonapis/gstinbypan?pan=" + self.pan_id + "&gstin_details=yes"
                response = requests.get(api_endpoint, headers=headers)
                result = response.json()
                data = result['data']
                if not response.json()['error']:
                    sl_no = 1
                    customer_ids.pan_response_ids = False
                    for gstin in data:
                        try:
                            address = list(gstin['pradr']['addr'].values())
                        except KeyError:
                            address = ""
                        self.env['pan.response.data'].create({
                            'res_partner_id': customer_ids.id,
                            'gstin_id': gstin['gstin'],
                            'address': str(', '.join(address)),
                            'sl_no': sl_no
                        })
                        sl_no += 1

                    notification = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Success'),
                            'type': 'success',
                            'message': 'GSTIN info fetched Successfully',
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
                else:
                    raise UserError(response.json()['message'])
