from odoo import models, fields
import requests
import json
from odoo.exceptions import ValidationError


class MailerCloudApiSync(models.Model):
    _name = 'mailer.cloud.api.sync'

    api_key = fields.Char(string='Api Key', required=True)
    active = fields.Boolean(string='Check')
    email = fields.Char(string='Email')
    name = fields.Char(string="Name")
    plan = fields.Char(string='Plan')
    remaining_contacts = fields.Integer(string='Remaining Contacts')
    total_contacts = fields.Integer(string='Total Contacts')
    used_contacts = fields.Integer(string='Used Contacts')
    list_id = fields.Many2one('mailer.cloud.list', string='List')
    contact_mapping_ids = fields.One2many('contact.sync', 'sync_id')
    contact_sync_active = fields.Boolean()
    contact_sync_time = fields.Datetime()

    def action_sync(self):
        # test connection api
        self.write({'contact_mapping_ids': [(5, 0, 0)]})
        try:
            url = "https://cloudapi.mailercloud.com/v1/client/plan"

            payload = ""
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }

            response = requests.request("GET", url, headers=headers,
                                        data=payload)
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
        # getting list of particular api
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

            response = requests.request("POST", url, headers=headers,
                                        data=payload)
            if response.status_code == 200:
                for rec in response.json()['data']:
                    self.env['mailer.cloud.list'].create({
                        'name': rec['name'],
                        'mailer_cloud_id': rec['id'],
                        'authorization_id': user,
                    })
            elif response.status_code == 400:
                raise ValidationError(response.json()['error']['message'])
            elif response.status_code == 401:
                raise ValidationError(response.json()['errors'][0]['message'])
        except Exception as e:
            raise ValidationError(e)

    def get_properties(self):
        # getting properties of particular api
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

            response = requests.request("POST", url, headers=headers,
                                        data=payload)
            if response.status_code == 200:
                for record in response.json()['data']:
                    if record['field_value'] not in self.env[
                        'mailer.cloud.properties'].search(
                        [('authorization_id', '=', False)]).mapped('name'):
                        if record['field_type'] == 'Text':
                            type_name = 'text'
                        elif record['field_type'] == 'Number':
                            type_name = 'number'
                        elif record['field_type'] == 'Date':
                            type_name = 'date'
                        elif record['field_type'] == 'Textarea':
                            type_name = 'textarea'
                        self.env.cr.execute("""INSERT INTO mailer_cloud_properties(mailer_cloud_id,name,type,authorization_id)
                                                                                        VALUES('%s','%s','%s',%s)""" % (
                            record['id'], record['field_value'], type_name,
                            self.id))
            elif response.status_code == 400:
                raise ValidationError(response.json()['error']['message'])
            elif response.status_code == 401:
                raise ValidationError(response.json()['errors'][0]['message'])
        except Exception as e:
            raise ValidationError(e)

    def action_contact_sync(self):
        # for syncing contacts
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
                                      i].id)]).mailer_cloud_id != False:
                            contact_details_dict['custom_fields'] = {
                                self.contact_mapping_ids.mapped(
                                    'property_id.mailer_cloud_id')[i]:
                                    self.env['res.partner'].search_read(
                                        [('id', '=', j.id)], [
                                            self.contact_mapping_ids.mapped(
                                                'contact_fields')[i]])[0][
                                        self.contact_mapping_ids.mapped(
                                            'contact_fields')[i]] or ' '}
                            for key, value in contact_details_dict[
                                'custom_fields'].items():
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
                                    contact_details_dict.update(
                                        {key: round(value)})
                    contact_details.append(contact_details_dict)
                url = "https://cloudapi.mailercloud.com/v1/contacts/batch"
                payload = json.dumps({
                    "contacts": contact_details,
                    "list_id": self.list_id.mailer_cloud_id
                })
                headers = {
                    'Authorization': self.api_key,
                    'Content-Type': 'application/json'
                }
                response = requests.request("POST", url, headers=headers,
                                            data=payload)
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
