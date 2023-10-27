# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
import requests
from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

TIMEOUT = 20


class ResPartner(models.Model):
    """Inherit res_partner for integrating contacts with Google"""
    _inherit = 'res.partner'

    google_resource = fields.Char('Google Contact Id',
                               help='Contact Unique identifier', readonly=True)
    google_etag = fields.Char(
        'Google Etag', help='Contact Version control key', readonly=True)
    first_name = fields.Char(
        'First Name', help='Enter the first name of the person.')
    last_name = fields.Char(
        'Last Name', help='Enter the last name of the person.')

    def action_export_google_contacts(self):
        """Export Contacts FROM Google TO ODOO"""
        current_uid = self._context.get('uid')
        user_id = self.env['res.users'].browse(current_uid)
        company_id = user_id.company_id
        partner_ids = self.env['res.partner'].sudo().browse(
            self.env.context.get('active_ids'))
        for partner in partner_ids:
            header = {
                'Authorization':
                    f'Bearer {company_id.contact_company_access_token}',
                'Content-Type': 'application/json'
            }
            contact_payload = {
                'names': [
                    {
                        'givenName': partner.first_name or partner.name,
                        'familyName': partner.last_name or ''
                    }
                ],
                'emailAddresses': [
                    {
                        'value': partner.email or '',
                        'type': 'work'
                    }
                ],
                'phoneNumbers': [
                    {
                        'value': partner.phone or '',
                        'type': 'work'
                    }
                ],
                'addresses': [
                    {
                        'streetAddress': partner.street or '',
                        'city': partner.city or '',
                        'region': partner.state_id.name or '',
                        'postalCode': partner.zip or '',
                        'country': partner.country_id.name or '',
                        'type': 'work'
                    }
                ],
                'organizations': [
                    {
                        'name': partner.company_id.name or '',
                        'title': partner.title or '',
                        'type': 'work'
                    }
                ]
            }
            if partner.google_etag:
                contact_resource_name = partner.google_resource
                contact_payload['resourceName'] = contact_resource_name
                contact_payload['etag'] = partner.google_etag
                url = (
                    f"https://people.googleapis.com/v1/{contact_resource_name}:updateContact?"
                    "updatePersonFields=emailAddresses,names,phoneNumbers,"
                    "addresses,organizations,userDefined&"
                    "prettyPrint=false"
                )
                response = requests.patch(url, headers=header,
                                          json=contact_payload)
                if response.status_code == 200:
                    partner.write({
                        'google_resource': response.json().get('resourceName'),
                        'google_etag': response.json().get('etag')
                    })
                    _logger.info("Contact updated successfully!")
                else:
                    error_message = f"Failed to update contact. Error: {response.text}"
                    raise ValidationError(error_message)
            else:
                url = 'https://people.googleapis.com/v1/people:createContact'
                result = requests.post(url, headers=header,
                                       json=contact_payload)
                if result.status_code == 200:
                    partner.write({
                        'google_resource': result.json().get('resourceName'),
                        'google_etag': result.json().get('etag')
                    })
                    _logger.info("Contact exported successfully!")
                else:
                    error_message = f"Failed to export contact. Error: {result.text}"
                    raise ValidationError(error_message)

    def action_delete_google_contact(self):
        """Deleting a contact from Google Contacts"""
        current_uid = self._context.get('uid')
        user_id = self.env['res.users'].browse(current_uid)
        company_id = user_id.company_id
        partner_ids = self.env['res.partner'].sudo().browse(
            self.env.context.get('active_ids'))
        for partner in partner_ids:
            contact_resource_name = partner.google_resource
            if not contact_resource_name:
                _logger.warning(
                    "Partner %s does not have a Google contact resource name.",
                    partner.name)
                continue
            url = f"https://people.googleapis.com/v1/{contact_resource_name}:deleteContact"
            headers = {
                'Authorization': f'Bearer {company_id.contact_company_access_token}',
                'Content-Type': 'application/json'
            }
            response = requests.delete(url, headers=headers)
            if response.status_code == 200:
                _logger.info("Contact deleted successfully!")
                partner.google_resource = ''
                partner.google_etag = ''
                partner.unlink()
            elif response.status_code == 404:
                _logger.warning(
                    "Contact not found in Google. Removing local reference.")
                partner.google_resource = ''
                partner.google_etag = ''
            else:
                error_message = f"Failed to delete contact. Error: {response.text}"
                raise ValidationError(error_message)
