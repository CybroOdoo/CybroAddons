# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
import json
import requests
from odoo import models, fields
from odoo.exceptions import ValidationError


class MailerCloudApiSync(models.Model):
    """
        Model representing the synchronization configuration for Mailer Cloud API.

        This model stores information about the Mailer Cloud API synchronization, including the API key,
        synchronization status, user details, plan information, associated mailing list, contact mappings,
        and synchronization activity.
        """
    _name = 'mailer.cloud.api.sync'
    _description = 'Mail Cloud API'

    api_key = fields.Char(
        string='Api Key',
        required=True,
        help='API key for connecting to Mailer Cloud.')
    active = fields.Boolean(
        string='Active',
        help='Check to activate the Mailer Cloud API synchronization.')
    email = fields.Char(
        string='Email',
        help='Email associated with the Mailer Cloud API user.')
    name = fields.Char(
        string="Name",
        help='Name associated with the Mailer Cloud API user.')
    plan = fields.Char(
        string='Plan',
        help='Current plan of the Mailer Cloud API user.')
    remaining_contacts = fields.Integer(
        string='Remaining Contacts',
        help='Remaining contact quota in the Mailer Cloud API user\'s plan.')
    total_contacts = fields.Integer(
        string='Total Contacts',
        help='Total contact quota in the Mailer Cloud API user\'s plan.')
    used_contacts = fields.Integer(
        string='Used Contacts',
        help='Number of contacts used in the Mailer Cloud API user\'s plan.')
    list_id = fields.Many2one(
        'mailer.cloud.list', string='Mailing List',
        help='Default mailing list associated with the Mailer Cloud API user.')
    contact_mapping_ids = fields.One2many(
        'contact.sync', 'sync_id', string='Contact Mapping Ids',
        help='Mappings between Odoo contact fields and Mailer Cloud properties for synchronization.')
    contact_sync_active = fields.Boolean(string='Contact Sync Active',
                                         help='Check to activate contact synchronization with Mailer Cloud.')
    contact_sync_time = fields.Datetime(string='Contact Sync time',
                                        help='Timestamp of the last contact synchronization activity.')

    def action_sync(self):
        """
            Test connection to Mailer Cloud API and synchronize information.

            This function tests the connection to the Mailer Cloud API and retrieves information
            about the API user's plan. It updates the relevant fields in the current record and triggers
            synchronization of lists and properties associated with the API user.

            :raises: ValidationError if there is an issue with the API connection or synchronization process.
            """
        self.write({'contact_mapping_ids': [(5, 0, 0)]})
        try:
            url = "https://cloudapi.mailercloud.com/v1/client/plan"
            payload = ""
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                self.write({
                    'email': response.json()['data']['email'],
                    'name': response.json()['data']['name'],
                    'plan': response.json()['data']['plan'],
                    'remaining_contacts': response.json()['data'][
                        'remaining_contacts'],
                    'total_contacts': response.json()['data'][
                        'total_contacts'],
                    'used_contacts': response.json()['data']['used_contacts'],
                    'active': True,
                    'contact_mapping_ids':
                        [(0, 0, {'property_id': self.env.ref(
                            'mailer_cloud_connector.property_data_name').id,
                                 'contact_fields': 'name'}),
                         (0, 0, {'property_id': self.env.ref(
                             'mailer_cloud_connector.property_data_email').id,
                                 'contact_fields': 'email'})]
                })
                self.get_list(self.id)
                self.get_properties()
            else:
                raise ValidationError(response.json()['errors'][0]['message'])
        except Exception as e:
            raise ValidationError(e)

    def get_list(self, user):
        """
            Retrieve Mailer Cloud lists associated with the current API user.

            This function sends a request to the Mailer Cloud API to retrieve lists related to the
            current API's authorization. It processes the response and creates records in the 'mailer.cloud.list'
            model in Odoo.

            :param user: The authorization user associated with the lists.
            :raises: ValidationError if there is an issue with the retrieval or record creation process.
            """
        self.env['mailer.cloud.list'].search([]).unlink()
        try:
            url = "https://cloudapi.mailercloud.com/v1/lists/search"
            payload = json.dumps({
                "limit": 100,
                "list_type": 1,
                "page": 1,
                "search_name": "",
                "sort_field": "name",
                "sort_order": "asc"
            })
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 200:
                for rec in response.json()['data']:
                    self.env['mailer.cloud.list'].create({
                        'name': rec['name'],
                        'mailer_cloud': rec['id'],
                        'authorization_id': user,
                    })
            elif response.status_code == 400:
                raise ValidationError(response.json()['error']['message'])
            elif response.status_code == 401:
                raise ValidationError(response.json()['errors'][0]['message'])
        except Exception as e:
            raise ValidationError(e)

    def get_properties(self):
        """
            Retrieve Mailer Cloud contact properties associated with the current API.

            This function sends a request to the Mailer Cloud API to retrieve contact properties
            related to the current API's authorization. It processes the response and inserts
            new properties into the 'mailer.cloud.properties' model in Odoo.

            :raises: ValidationError if there is an issue with the retrieval or insertion process.
            """
        try:
            url = "https://cloudapi.mailercloud.com/v1/contact/property/search"
            payload = json.dumps({
                "limit": 100,
                "page": 1,
                "search": ""
            })
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 200:
                for record in response.json()['data']:
                    if record['field_value'] not in self.env['mailer.cloud.properties'].search(
                            [('authorization_id', '=', False)]).mapped('name'):
                        if record['field_type'] == 'Text':
                            type_name = 'text'
                        elif record['field_type'] == 'Number':
                            type_name = 'number'
                        elif record['field_type'] == 'Date':
                            type_name = 'date'
                        elif record['field_type'] == 'Textarea':
                            type_name = 'textarea'
                        self.env.cr.execute("""INSERT INTO mailer_cloud_properties(
                        mailer_cloud,name,type,authorization_id)VALUES('%s','%s','%s',%s)""" % (
                            record['id'], record['field_value'], type_name, self.id))
            elif response.status_code == 400:
                raise ValidationError(response.json()['error']['message'])
            elif response.status_code == 401:
                raise ValidationError(response.json()['errors'][0]['message'])
        except Exception as e:
            raise ValidationError(e)

    def action_contact_sync(self):
        """
            Synchronize contacts with Mailer Cloud.

            This function synchronizes contacts from Odoo's 'res.partner' model to Mailer Cloud.
            It constructs the contact details and sends a batch request to the Mailer Cloud
            API for contact synchronization.

            :raises: ValidationError if there is an issue with the synchronization process.
            """
        if self.list_id:
            try:
                contact_details = []
                contact_details.clear()
                res = self.env['res.partner'].search([], limit=50)
                for j in res:
                    contact_details_dict = {}
                    contact_details_dict.clear()
                    for i in range(
                            len(self.contact_mapping_ids.mapped(
                                'property_id.name'))):
                        if self.env['mailer.cloud.properties'].search(
                                [('id', '=',
                                  self.contact_mapping_ids.mapped(
                                      'property_id')[
                                      i].id)]).mailer_cloud:
                            contact_details_dict['custom_fields'] = {
                                self.contact_mapping_ids.mapped(
                                    'property_id.mailer_cloud')[i]: self.env['res.partner'].search_read(
                                    [('id', '=', j.id)], [self.contact_mapping_ids.mapped('contact_fields')[i]])[0][
                                                                        self.contact_mapping_ids.mapped(
                                                                            'contact_fields')[i]] or ' '}
                            for key, value in contact_details_dict['custom_fields'].items():
                                if isinstance(value, float):
                                    contact_details_dict[
                                        'custom_fields'].update(
                                        {key: round(value)})
                        else:
                            contact_details_dict[
                                self.contact_mapping_ids.mapped(
                                    'property_id.name')[
                                    i]] = self.env['res.partner'].search_read(
                                [('id', '=', j.id)], [
                                    self.contact_mapping_ids.mapped(
                                        'contact_fields')[i]])[0][
                                              self.contact_mapping_ids.mapped(
                                                  'contact_fields')[i]] or ' '
                            for key, value in contact_details_dict.items():
                                if isinstance(value, float):
                                    contact_details_dict.update({key: round(value)})
                    contact_details.append(contact_details_dict)
                url = "https://cloudapi.mailercloud.com/v1/contacts/batch"
                payload = json.dumps({
                    "contacts": contact_details,
                    "list_id": self.list_id.mailer_cloud
                })
                headers = {
                    'Authorization': self.api_key,
                    'Content-Type': 'application/json'
                }
                response = requests.request("POST", url, headers=headers, data=payload)
                if response.status_code == 200:
                    self.write({
                        'contact_sync_active': True,
                        'contact_sync_time': fields.Datetime.now()
                    })
                elif response.status_code == 400:
                    raise ValidationError(response.json()['errors']['message'])
                elif response.status_code == 401:
                    raise ValidationError(
                        response.json()['errors'][0]['message'])
            except Exception as e:
                raise ValidationError(e)
        else:
            raise ValidationError("Please Choose a List")
