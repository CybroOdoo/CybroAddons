# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import fields, models
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
                pipedrive_reference = self.env.user.company_id.create_contact(
                    self.env['res.partner'].browse(
                        vals['partner_id']))
            data['person_id'] = int(pipedrive_reference)
        if 'expected_revenue' in vals.keys():
            data['value'] = {
                'amount': vals['expected_revenue'],
                'currency': self.env.company.currency_id.name
            }
        if self.pipedrive_reference and data:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.patch(
                url=f'https://api.pipedrive.com/v1/leads/'
                    f'{self.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers, data=json.dumps(data))
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().write(vals)

    def unlink(self):
        """Inherited to add the code for deleting the product from Pipedrive"""
        if self.pipedrive_reference:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.delete(
                url=f'https://api.pipedrive.com/v1/leads/'
                    f'{self.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers)
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().unlink()
