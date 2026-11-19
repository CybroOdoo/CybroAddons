# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import json
import requests
from odoo import Command, fields, models
from odoo.exceptions import ValidationError


class MailerCloudApiSync(models.Model):
    """
    Model representing the synchronization configuration for Mailercloud API.

    This model stores information about the Mailercloud API synchronization, including the API key,
    synchronization status, user details, plan information, associated mailing list, contact mappings,
    and synchronization activity.
    """
    _name = 'mailer.cloud.api.sync'
    _description = 'Mailercloud API Sync'

    api_key = fields.Char(
        required=True,
        groups='base.group_system',
        help='API key for connecting to Mailercloud.')
    active = fields.Boolean(
        help='Check to activate the Mailercloud API synchronization.')
    email = fields.Char(
        help='Email associated with the Mailercloud API user.')
    name = fields.Char(
        help='Name associated with the Mailercloud API user.')
    plan = fields.Char(
        help='Current plan of the Mailercloud API user.')
    remaining_contacts = fields.Integer(
        help='Remaining contact quota in the Mailercloud API user\'s plan.')
    total_contacts = fields.Integer(
        help='Total contact quota in the Mailercloud API user\'s plan.')
    used_contacts = fields.Integer(
        help='Number of contacts used in the Mailercloud API user\'s plan.')
    list_id = fields.Many2one(
        'mailer.cloud.list', string='Mailing List',
        help='Default mailing list associated with the Mailercloud API user.')
    contact_mapping_ids = fields.One2many(
        'contact.sync', 'sync_id', string='Contact Mapping Ids',
        help='Mappings between Odoo contact fields and Mailercloud properties for synchronization.')
    contact_sync_active = fields.Boolean(
        help='Check to activate contact synchronization with Mailercloud.')
    contact_sync_time = fields.Datetime(
        string='Contact Sync time',
        help='Timestamp of the last contact synchronization activity.')

    def action_sync(self):
        """
        Test connection to Mailercloud API and synchronize information.

        This function tests the connection to the Mailercloud API and retrieves information
        about the API user's plan. It updates the relevant fields in the current record and triggers
        synchronization of lists and properties associated with the API user.

        :raises: ValidationError if there is an issue with the API connection or synchronization process.
        """
        self.get_properties()
        self.write({'contact_mapping_ids': [Command.clear()]})
        try:
            url = "https://cloudapi.mailercloud.com/v1/client/plan"
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.request("GET", url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json().get('data', {})
                name_prop = self.env.ref('mailer_cloud_connector.property_data_name', raise_if_not_found=False)
                email_prop = self.env.ref('mailer_cloud_connector.property_data_email', raise_if_not_found=False)
                mappings = []
                if name_prop:
                    mappings.append(Command.create({
                        'property_id': name_prop.id,
                        'contact_fields': 'name'
                    }))
                if email_prop:
                    mappings.append(Command.create({
                        'property_id': email_prop.id,
                        'contact_fields': 'email'
                    }))

                self.write({
                    'email': data.get('email'),
                    'name': data.get('name'),
                    'plan': data.get('plan'),
                    'remaining_contacts': data.get('remaining_contacts', 0),
                    'total_contacts': data.get('total_contacts', 0),
                    'used_contacts': data.get('used_contacts', 0),
                    'active': True,
                    'contact_mapping_ids': mappings,
                })
                self.get_list(self.id)
                self.get_properties()
            else:
                errors = response.json().get('errors', [{}])
                msg = errors[0].get('message', 'Error') if isinstance(errors, list) and errors else str(errors)
                raise ValidationError(msg)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e) from e

    def get_list(self, user):
        """
        Retrieve Mailercloud lists associated with the current API user.

        This function sends a request to the Mailercloud API to retrieve lists related to the
        current API's authorization. It processes the response and creates records in the 'mailer.cloud.list'
        model in Odoo.

        :param user: The authorization user ID associated with the lists.
        :raises: ValidationError if there is an issue with the retrieval or record creation process.
        """
        self.env['mailer.cloud.list'].search([('authorization_id', '=', user)]).unlink()
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
            response = requests.request(
                "POST", url, headers=headers, data=payload, timeout=30)
            if response.status_code == 200:
                for rec in response.json().get('data', []):
                    self.env['mailer.cloud.list'].create({
                        'name': rec.get('name'),
                        'mailer_cloud': rec.get('id'),
                        'authorization_id': user,
                    })
            elif response.status_code == 400:
                raise ValidationError(response.json().get('error', {}).get('message', 'Bad Request'))
            elif response.status_code == 401:
                errors = response.json().get('errors', [{}])
                msg = errors[0].get('message', 'Unauthorized') if isinstance(errors, list) and errors else str(errors)
                raise ValidationError(msg)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e) from e

    def get_properties(self):
        """
        Retrieve Mailercloud contact properties associated with the current API.

        This function sends a request to the Mailercloud API to retrieve contact properties
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
            response = requests.request(
                "POST", url, headers=headers, data=payload, timeout=30)
            if response.status_code == 200:
                name_list = self.env['mailer.cloud.properties'].search(
                    [('authorization_id', 'in', [False, self.id])]).mapped('name')
                for record in response.json().get('data'):
                    field_val = record.get('field_value')
                    type_name = ''
                    if record.get('field_type') == 'Text':
                        type_name = 'text'
                    elif record.get('field_type') == 'Number':
                        type_name = 'number'
                    elif record.get('field_type') == 'Date':
                        type_name = 'date'
                    elif record.get('field_type') == 'Textarea':
                        type_name = 'textarea'
                    if field_val and field_val not in name_list:
                        self.env['mailer.cloud.properties'].create({
                            'mailer_cloud': record.get('id'),
                            'name': field_val,
                            'type': type_name,
                            'authorization_id': self.id,
                        })
            elif response.status_code == 400:
                raise ValidationError(response.json().get('error', {}).get('message', 'Bad Request'))
            elif response.status_code == 401:
                errors = response.json().get('errors', [{}])
                msg = errors[0].get('message', 'Unauthorized') if isinstance(errors, list) and errors else str(errors)
                raise ValidationError(msg)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e) from e

    def action_contact_sync(self):
        """
        Synchronize contacts with Mailercloud.

        This function synchronizes contacts from Odoo's 'res.partner' model to Mailercloud.
        It constructs the contact details and sends batch requests to the Mailercloud
        API for contact synchronization.

        :raises: ValidationError if there is an issue with the synchronization process.
        """
        if not self.list_id:
            raise ValidationError(self.env._('Please Choose a List'))
        try:
            contact_details = []
            partners = self.env['res.partner'].search([('email', '!=', False)])
            for partner in partners:
                contact_details_dict = {}
                for mapping in self.contact_mapping_ids:
                    field_name = mapping.contact_fields
                    field_val = partner[field_name] if field_name in partner._fields else False
                    if isinstance(field_val, float):
                        field_val = round(field_val)
                    elif not field_val:
                        field_val = ''
                    else:
                        field_val = str(field_val) if not isinstance(field_val, (int, str, bool)) else field_val

                    if mapping.property_id.mailer_cloud:
                        if 'custom_fields' not in contact_details_dict:
                            contact_details_dict['custom_fields'] = {}
                        contact_details_dict['custom_fields'][mapping.property_id.mailer_cloud] = field_val
                    else:
                        contact_details_dict[mapping.property_id.name] = field_val
                if 'email' not in contact_details_dict and partner.email:
                    contact_details_dict['email'] = partner.email
                contact_details.append(contact_details_dict)

            batch_size = 100
            batches = (
                [contact_details[i:i + batch_size] for i in range(0, len(contact_details), batch_size)]
                if contact_details else [[]]
            )
            for batch in batches:
                url = "https://cloudapi.mailercloud.com/v1/contacts/batch"
                payload = json.dumps({
                    "contacts": batch,
                    "list_id": self.list_id.mailer_cloud
                })
                headers = {
                    'Authorization': self.api_key,
                    'Content-Type': 'application/json'
                }
                response = requests.request(
                    "POST", url, headers=headers, data=payload, timeout=30)
                if response.status_code == 200:
                    continue
                if response.status_code == 400:
                    errors = response.json().get('errors', {})
                    msg = errors.get('message') if isinstance(errors, dict) else str(errors)
                    raise ValidationError(msg or 'Bad Request')
                if response.status_code == 401:
                    errors = response.json().get('errors', [{}])
                    msg = errors[0].get('message', 'Unauthorized') if isinstance(errors, list) and errors else str(errors)
                    raise ValidationError(msg)
                raise ValidationError(
                    self.env._('Failed to synchronize contacts: status %s', response.status_code))

            self.write({
                'contact_sync_active': True,
                'contact_sync_time': fields.Datetime.now()
            })
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e) from e
