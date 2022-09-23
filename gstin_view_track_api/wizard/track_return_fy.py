# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-August Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vyshnav AR (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests


class TrackReturnWiz(models.TransientModel):
    _name = 'track.return.api'

    @api.model
    def year_selection(self):
        year = 2017
        year_list = []
        while year != fields.Date.today().year + 2:
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    from_year = fields.Selection(year_selection, string='Start Year', required=True)
    to_year = fields.Selection(year_selection, string='End Year', required=True)

    @api.onchange('from_year')
    def _onchange_from_year(self):
        try:
            if self.from_year:
                self.to_year = str(int(self.from_year) + 1)
        except ValueError:
            self.to_year = False
            self.from_year = False
            raise UserError("Please select a Valid Range")

    @api.onchange('to_year')
    def _onchange_to_year(self):
        try:
            if self.to_year:
                self.from_year = str(int(self.to_year) - 1)
        except ValueError:
            self.to_year = False
            self.from_year = False
            raise UserError("Please select a Valid Range")

    def action_track(self):
        customer_ids = self.env['res.partner'].search([('id', '=', self.env.context.get('active_id'))])

        for rec in customer_ids:
            if not rec.vat:
                raise UserError("GST Identification Number not assigned")

            url = "https://pro.mastersindia.co/oauth/access_token"

            username = self.env['ir.config_parameter'].get_param('autotax_username')
            password = self.env['ir.config_parameter'].get_param('autotax_password')
            client_id = self.env['ir.config_parameter'].get_param('autotax_client_id')
            client_secret = self.env['ir.config_parameter'].get_param('autotax_client_secret')

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
                    api_endpoint = "https://commonapi.mastersindia.co/commonapis/trackReturns?gstin=" + rec.vat + "&fy=" + str(
                        self.from_year) + '-' + self.to_year[2:]
                    response = requests.get(api_endpoint, headers=headers)
                    result = response.json()
                    if result['error']:
                        raise UserError(result['message'])
                    data = result.get('data')
                    filed_list = data.get('EFiledlist')
                    for res in filed_list:
                        response_ids = self.env['response.data'].sudo().create({
                            'des': rec.id,
                            'arn': res.get('arn'),
                            'ret_prd': fields.datetime.strptime(str(res.get('ret_prd')), '%m%Y'),
                            'mof': res.get('mof'),
                            'dof': res.get('dof'),
                            'rtn_type': res.get('rtntype'),
                            'status': res.get('status'),
                            'valid': res.get('valid')
                        })
                if not response.json()['error']:
                    notification = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Success'),
                            'type': 'success',
                            'message': 'GSTIN Returns Data Fetched Successfully',
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
