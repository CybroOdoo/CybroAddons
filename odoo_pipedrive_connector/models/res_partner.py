# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Inherits Res Partner for including Pipedrive fields and functions"""
    _inherit = 'res.partner'

    pipedrive_reference = fields.Char(help="Pipedrive Id of the Partner")

    def write(self, vals):
        if (self.env.context.get('update_from_pipedrive') or
                self.env.context.get('skip_pipedrive_sync')):
            return super().write(vals)

        result = super().write(vals)

        for partner in self:
            if not partner.pipedrive_reference:
                continue

            data = {}

            if 'name' in vals:
                data['name'] = partner.name
            if 'email' in vals:
                data['email'] = [{'value': partner.email, 'primary': True}]

            if not data:
                continue

            response = requests.put(
                f'https://api.pipedrive.com/v1/persons/{partner.pipedrive_reference}',
                params={'api_token': self.env.company.api_key},
                json=data, timeout=10
            )

            if response.json().get('error'):
                raise ValidationError(response.json()['error'])

        return result

    @api.ondelete(at_uninstall=False)
    def _unlink_pipedrive_contact(self):
        """Delete the partner from Pipedrive before it is removed from Odoo"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        for rec in self:
            pipedrive_contact = self.env['pipedrive.record'].sudo().search(
                [('record_type', '=', 'partner'), ('odoo_ref', '=', rec.id)])
            if pipedrive_contact:
                response = requests.delete(
                    url=f'https://api.pipedrive.com/v1/persons/'
                        f'{pipedrive_contact.pipedrive_reference}',
                    params={
                        'api_token': self.env.company.api_key,
                    }, timeout=10, headers=headers)
                if 'error' in response.json().keys():
                    raise ValidationError(
                        response.json()['error'])

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        if not self.env.company.contact_synced:
            return res

        for rec in res:
            existing = self.env['pipedrive.record'].sudo().search([
                ('record_type', '=', 'partner'),
                ('odoo_ref', '=', rec.id)
            ], limit=1)

            if existing or rec.pipedrive_reference:
                continue

            data = {
                'name': rec.name,
                'email': rec.email,
                'phone': rec.phone
            }

            response = requests.post(
                'https://api.pipedrive.com/v1/persons',
                params={'api_token': self.env.company.api_key},
                json=data, timeout=10
            )

            res_data = response.json()
            if not res_data.get('success'):
                raise ValidationError(res_data.get('error'))

            pid = str(res_data['data']['id'])

            rec.pipedrive_reference = pid

            self.env['pipedrive.record'].sudo().create({
                'pipedrive_reference': pid,
                'record_type': 'partner',
                'odoo_ref': rec.id
            })

        return res
