# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
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
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Inherits Res Users for including Pipedrive fields and fuctions"""
    _inherit = 'res.partner'

    pipedrive_reference = fields.Char(string='Pipedrive Reference',
                                      help="Pipedrive Id of the Partner")

    def write(self, vals):
        if self.env.context.get('skip_pipedrive_sync'):
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

    def unlink(self):
        """Inherited to delete the partner from Pipedrive"""
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
