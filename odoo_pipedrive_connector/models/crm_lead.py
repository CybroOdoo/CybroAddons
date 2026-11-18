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
import json
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    """Inherits crm Lead for including Pipedrive fields and functions"""
    _inherit = 'crm.lead'

    pipedrive_reference = fields.Char(help="Pipedrive reference of the lead")

    def write(self, vals):
        """Inherited to add the code for updating the product details in
        Pipedrive"""
        data = {}
        if 'name' in vals.keys():
            data['title'] = vals['name']
        if 'partner_id' in vals.keys():
            pipedrive_reference = self.env['res.partner'].browse(
                vals['partner_id']).pipedrive_reference
            if not pipedrive_reference:
                pipedrive_reference = (
                    self.env.company.sudo().create_contact(
                        self.env['res.partner'].sudo().browse(
                            vals['partner_id'])))
            data['person_id'] = int(pipedrive_reference)
        if 'expected_revenue' in vals.keys():
            data['value'] = {
                'amount': vals['expected_revenue'],
                'currency': self.env.company.currency_id.name
            }
        for rec in self:
            pipedrive_lead = self.env['pipedrive.record'].sudo().search(
                [('record_type', '=', 'lead'), ('odoo_ref', '=', rec.id)])
            if pipedrive_lead and data:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                response = requests.patch(
                    url=f'https://api.pipedrive.com/v1/leads/'
                        f'{rec.pipedrive_reference}',
                    params={
                        'api_token': rec.env.company.api_key,
                    }, timeout=10, headers=headers, data=json.dumps(data))
                if 'error' in response.json().keys():
                    raise ValidationError(
                        response.json()['error'])
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_pipedrive_lead(self):
        """Delete the lead from Pipedrive before it is removed from Odoo"""
        for rec in self:
            pipedrive_lead = self.env['pipedrive.record'].sudo().search(
                [('record_type', '=', 'lead'), ('odoo_ref', '=', rec.id)])
            if pipedrive_lead:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                response = requests.delete(
                    url=f'https://api.pipedrive.com/v1/leads/'
                        f'{pipedrive_lead.pipedrive_reference}',
                    params={
                        'api_token': self.env.company.api_key,
                    }, timeout=10, headers=headers)
                if 'error' in response.json().keys():
                    raise ValidationError(
                        response.json()['error'])

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited to add the lead to pipedrive"""
        res = super().create(vals_list)

        if self.env.company.lead_synced:
            for rec in res:
                # Check if this record is already synced
                if self.env['pipedrive.record'].search([
                    ('record_type', '=', 'lead'),
                    ('odoo_ref', '=', rec.id)
                ]):
                    continue

                # Check if partner exists
                if rec.partner_id:
                    # Ensure partner has pipedrive reference
                    pipedrive_contact_ref = rec.partner_id.pipedrive_reference
                    if not pipedrive_contact_ref:
                        pipedrive_contact_ref = (
                            self.env.company.sudo().create_contact(
                                rec.partner_id.sudo()))

                    data = {
                        'title': rec.name,
                        'person_id': int(pipedrive_contact_ref),
                        'value': {
                            'amount': rec.expected_revenue or 0.0,
                            'currency': self.env.company.currency_id.name
                        }
                    }
                    response = requests.post(
                        url='https://api.pipedrive.com/v1/leads',
                        params={
                            'api_token': self.env.company.api_key,
                        }, json=data, timeout=10)
                    response_data = response.json()
                    if not response_data.get('success'):
                        error_msg = response_data.get('error', 'Unknown error')
                        error_info = response_data.get('error_info', '')
                        raise ValidationError(self.env._(
                            "%(error)s. %(info)s",
                            error=error_msg, info=error_info))
                    pipedrive_id = str(response_data['data']['id'])
                    # Assign pipedrive_reference to the created record
                    rec.pipedrive_reference = pipedrive_id
                    # Create the pipedrive.record entry
                    self.env['pipedrive.record'].sudo().create({
                        'pipedrive_reference': pipedrive_id,
                        'record_type': 'lead',
                        'odoo_ref': rec.id
                    })
        return res
