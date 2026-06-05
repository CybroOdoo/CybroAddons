# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import json
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Inherits Res Users for including Pipedrive fields and functions"""
    _inherit = 'res.partner'

    pipedrive_reference = fields.Char(string='Pipedrive Reference',
                                      help="Pipedrive Id of the Partner")

    def write(self, vals):
        """Inherited to update the partner details in Pipedrive"""
        if self.env.context.get('skip_pipedrive_sync'):
            return super().write(vals)
        data = {}
        if 'name' in vals.keys():
            data['name'] = vals['name']
        if 'email' in vals.keys():
            data['email'] = [{'value': vals['email'], 'primary': True}]
        if 'phone' in vals.keys():
            data['phone'] = [{'value': vals['phone'], 'primary': True}]
        pipedrive_contact = self.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'partner'), ('odoo_ref', '=', self.id)])
        if pipedrive_contact and data:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.put(
                url=f'https://api.pipedrive.com/v1/persons/'
                    f'{pipedrive_contact.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers, data=json.dumps(data))
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().write(vals)

    def unlink(self):
        """Inherited to delete the partner from Pipedrive"""
        if self.env.context.get('skip_pipedrive_sync'):
            return super().unlink()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        pipedrive_contact = self.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'partner'), ('odoo_ref', '=', self.id)])
        if pipedrive_contact:
            response = requests.delete(
                url=f'https://api.pipedrive.com/v1/persons/'
                    f'{pipedrive_contact.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers)
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited to add the contact to pipedrive"""
        res = super().create(vals_list)
        if self.env.context.get('skip_pipedrive_sync'):
            return res
        if self.env.company.contact_synced and self.env.company.api_key:
            for partner, vals in zip(res, vals_list):
                if partner.pipedrive_reference:
                    continue
                if self.env['pipedrive.record'].sudo().search([
                    ('record_type', '=', 'partner'),
                    ('odoo_ref', '=', partner.id)
                ], limit=1):
                    continue
                data = {
                    'name': vals.get('name') or partner.name
                }
                if vals.get('email'):
                    data['email'] = vals['email']
                if vals.get('phone'):
                    data['phone'] = vals['phone']
                response = requests.post(
                    url='https://api.pipedrive.com/v1/persons',
                    params={
                        'api_token': self.env.company.api_key,
                    }, json=data, timeout=10)
                if 'success' in response.json(
                ).keys() and not response.json()['success'] and 'error' in \
                        response.json(
                        ).keys():
                    raise ValidationError(
                        response.json()['error'])
                pipedrive_reference = response.json()['data']['id']
                self.env['pipedrive.record'].sudo().create({
                    'pipedrive_reference': pipedrive_reference,
                    'record_type': 'partner',
                    'odoo_ref': partner.id
                })
                partner.with_context(skip_pipedrive_sync=True).sudo().write({
                    'pipedrive_reference': pipedrive_reference
                })
        return res
