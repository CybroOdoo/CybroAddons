# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S (odoo@cybrosys.com)
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
###############################################################################
import json
import requests

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """
    Inherits the model Res Config Settings to extend the model and add extra
    fields and functionalities
    """
    _inherit = 'res.config.settings'

    api_key = fields.Char(string='API Key', help='API key to connect',
                          config_parameter='odoo_klaviyo_connector.api_key')
    import_data = fields.Boolean(string="Import List",
                                 help="Whether to import data from Klaviyo",
                                 config_parameter='odoo_klaviyo_connector.import_data')
    export_data = fields.Boolean(string="Export List",
                                 help="Whether to export data to Klaviyo",
                                 config_parameter='odoo_klaviyo_connector.export_data')

    def action_execute_operation(self):
        """
        This is the method action_execute_operation which is here used to
        execute the operations as to import and export datas from Klaviyo to
        Odoo and vice versa.
        """
        imported_records = 0
        exported_records = 0
        if self.import_data:
            import_list_data = self.action_test_connection(get_data=True)
            for klaviyo_list in import_list_data.json().get('data'):
                existing_record = self.env['mailing.list'].search(
                    [('klaviyo_id', '=', klaviyo_list.get('id'))])
                if not existing_record:
                    members_response = self.get_klaviyo_members(
                        user_id=klaviyo_list.get('id'))
                    self.create_mailing_list_and_contacts(
                        members_response=members_response,
                        klaviyo_list=klaviyo_list)
                    imported_records += 1
        if self.export_data:
            headers = {
                "accept": 'application/json',
                "revision": '2023-09-15',
                "content-type": 'application/json',
                'Authorization': f'Klaviyo-API-Key {self.api_key}',
            }
            lists_to_export = self.env['mailing.list'].search(
                [('klaviyo_id', '=', False)])
            for mailing_list in lists_to_export:
                self.export_mailing_list(mailing_list=mailing_list,
                                         headers=headers)
                exported_records += 1
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(
                    'Executed the operation successfully!'),
                'message': f'Successfully imported {imported_records} Records '
                           f'and exported {exported_records} Records',
                'sticky': True,
                'type': 'success'
            }
        }
        return notification

    def export_mailing_list(self, mailing_list, headers):
        """
        This is the method export_mailing_list which is responsible for
        exporting the mailing list to the Klaviyo and also creates the contacts
        in the corresponding mailing list.
        """
        url = "https://a.klaviyo.com/api/lists/"
        list_response = self.get_list_response(
            mailing_list=mailing_list, url=url, headers=headers)
        if list_response.status_code == 201:
            created_list_id = list_response.json().get('data').get('id')
            mailing_list.klaviyo_id = created_list_id
            for profile in mailing_list.contact_ids:
                create_profile_url = 'https://a.klaviyo.com/api/profiles/'
                profile_data = {
                    "data": {
                        "type": "profile",
                        "attributes": {
                            "email": profile.email,
                            "first_name": profile.name
                        }
                    }
                }
                response = requests.post(create_profile_url,
                                         json=profile_data,
                                         headers=headers, timeout=10)
                profile_id = False
                if response.status_code == 201:
                    profile_id = response.json().get("data").get("id")
                elif response.status_code == 409:
                    profile_id = response.json().get("errors")[0].get(
                        "meta").get("duplicate_profile_id")
                add_profile_list_url = f"https://a.klaviyo.com/api/lists/{created_list_id}/relationships/profiles/"
                profile_data = json.dumps({
                    "data": [
                        {
                            "type": "profile",
                            "id": profile_id
                        }
                    ]
                })
                requests.request("POST", add_profile_list_url,
                                 headers=headers,
                                 data=profile_data, timeout=10)

    def create_mailing_list_and_contacts(self, members_response, klaviyo_list):
        """
        This is the method create_mailing_list_and_contacts which will create
        the mailing list and contacts in odoo with the data get from the
        Klaviyo API
        """
        create_mailing_list = self.env['mailing.list'].create({
            'name': klaviyo_list.get('attributes').get('name'),
            'klaviyo_id': klaviyo_list.get('id'),
        })
        contacts = [
            self.env['mailing.contact'].create(
                {'email': record.get('email'),
                 'klaviyo_id': record.get('id')}).id
            for record in members_response.json().get('records')
        ]
        create_mailing_list.write(
            {'contact_ids': [(6, 0, contacts)]})

    def get_klaviyo_members(self, user_id):
        """
        This is the method get_klaviyo_members which returns the list of members
        in the list of the corresponding Klaviyo List
        """
        url = f"https://a.klaviyo.com/api/v2/group/{user_id}/members/all?api_key={self.api_key}"
        payload = {}
        headers = {
            'Accept': 'application/json'
        }
        members_response = requests.request("GET", url,
                                            headers=headers,
                                            data=payload,
                                            timeout=10)
        return members_response

    def get_list_response(self, mailing_list, url, headers):
        """
        This is the method get_list_response which is here used to return the
        all list in  the Klaviyo using the API
        """
        payload = {
            'data': {
                "type": 'list',
                "attributes": {
                    "name": mailing_list.name
                },
            }
        }
        list_response = requests.post(url, json=payload,
                                      headers=headers,
                                      timeout=10)
        return list_response

    def action_test_connection(self, get_data=False):
        """
        This is the method action_test_connection which is here used to test
        the connection to Klaviyo from odoo.
        """
        if self.api_key:
            url = "https://a.klaviyo.com/api/lists"
            payload = {}
            headers = {
                'revision': '2023-09-15',
                'Authorization': f'Klaviyo-API-Key {self.api_key}',
                'Accept': 'application/json'
            }
            response = requests.request("GET", url, headers=headers,
                                        data=payload, timeout=10)
            if get_data:
                return response
            return self.action_notify(
                True) if response.status_code == 200 else self.action_notify(
                False)
        raise ValidationError(_('Please enter the credentials'))

    def action_notify(self, success):
        """
        This is the method action_notify which will be called when connection is
        tested to klaviyo from odoo which this function return whether the
        connection is true or false
        """
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connection successful!') if success is True else _(
                    'Connection not successful!'),
                'message': 'Connection to Klaviyo is successful.' if success is True else 'Connection to Klaviyo is not successful.',
                'sticky': False,
                'type': 'success' if success is True else 'danger'
            }
        }
        return notification
