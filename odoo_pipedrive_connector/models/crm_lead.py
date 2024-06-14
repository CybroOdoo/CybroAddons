# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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


class CrmLead(models.Model):
    """Inherits crm Lead for including Pipedrive fields and functions"""
    _inherit = 'crm.lead'

    pipedrive_reference = fields.Char(string='Pipedrive Id',
                                      help="Pipedrive reference of the lead")

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
                    self.env.user.company_id.sudo().create_contact(
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
                        'api_token': rec.env.user.company_id.api_key,
                    }, timeout=10, headers=headers, data=json.dumps(data))
                if 'error' in response.json().keys():
                    raise ValidationError(
                        response.json()['error'])
        return super().write(vals)

    def unlink(self):
        """Inherited to add the code for deleting the product from Pipedrive"""
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
                        'api_token': self.env.user.company_id.api_key,
                    }, timeout=10, headers=headers)
                if 'error' in response.json().keys():
                    raise ValidationError(
                        response.json()['error'])
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited to add the lead to pipedrive"""
        res = super().create(vals_list)
        if self.env.company.lead_synced and not self.env['pipedrive.record'].search(
                [('record_type', '=', 'lead',), ('odoo_ref', '=', res.id)]):
            for lead in vals_list:
                if lead['partner_id']:
                    data = {
                        'title': lead['name'],
                        'person_id': int(self.env['pipedrive.record'].search(
                    [('record_type', '=', 'partner',),
                     ('odoo_ref', '=', lead['partner_id'])]).pipedrive_reference),
                        'value': {
                            'amount': lead[
                                'expected_revenue'] if 'expected_revenue'
                                                       in lead.keys() else 0.0,
                            'currency': self.env.company.currency_id.name
                        }
                    }
                    response = requests.post(
                        url='https://api.pipedrive.com/v1/leads',
                        params={
                            'api_token': self.env.company.api_key,
                        }, json=data, timeout=10)
                    if not response.json()['success']:
                        raise ValidationError(
                            response.json()['error'] + '. ' + response.json()[
                                'error_info'])
                    self.env['pipedrive.record'].sudo().create({
                        'pipedrive_reference': response.json()['data']['id'],
                        'record_type': 'lead',
                        'odoo_ref': res.id
                    })
        return res
