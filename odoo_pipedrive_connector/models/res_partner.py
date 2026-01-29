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


class ResPartner(models.Model):
    """Inherits Res Users for including Pipedrive fields and functions"""
    _inherit = 'res.partner'

    pipedrive_reference = fields.Char(string='Pipedrive Id',
                                      help="Pipedrive Id of the Partner")

    def write(self, vals):
        """Inherited to update the partner details in Pipedrive"""
        data = {}
        if 'name' in vals.keys():
            data['name'] = vals['name']
        if 'email' in vals.keys():
            data['email'] = [{'value': vals['email'], 'primary': True}]
        if 'phone' in vals.keys():
            data['phone'] = [{'value': vals['phone'], 'primary': True}]
        if self.pipedrive_reference and data:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.put(
                url=f'https://api.pipedrive.com/v1/persons/'
                    f'{self.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers, data=json.dumps(data))
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().write(vals)

    def unlink(self):
        """Inherited to delete the partner from Pipedrive"""
        if self.pipedrive_reference:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.delete(
                url=f'https://api.pipedrive.com/v1/persons/'
                    f'{self.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers)
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().unlink()
