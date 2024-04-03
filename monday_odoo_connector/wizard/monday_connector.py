# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models
from odoo.exceptions import ValidationError


class MondayConnector(models.TransientModel):
    _name = 'monday.connector'
    _description = 'Monday Connector'
    _rec_name = 'credential_id'

    credential_id = fields.Many2one('monday.credential', required="True",
                                    string="Monday Credentials",
                                    help="Select the credential for connecting"
                                         " with Monday.com")
    import_user = fields.Boolean(string="Import User",
                                 help="Check if you want to import user")
    import_board = fields.Boolean(string="Import Board",
                                  help="Check if you want to import board")
    import_group = fields.Boolean(string="Import Group",
                                  help="If you want to import the board, "
                                       "groups will also imported",
                                  readonly=True, default=True)
    import_item = fields.Boolean(string="Import Item",
                                 help="If you want to import the board, "
                                      "items will also imported",
                                 readonly=True, default=True)
    import_contact = fields.Boolean(string="Import Customer",
                                    help="Check if you want to import contact")

    def action_execute(self):
        """Function for executing Import and Export between Odoo and
        Monday.com"""
        if self.import_board:
            self.get_boards("https://api.monday.com/v2",
                            {"Authorization": self.credential_id.token})
        if self.import_user:
            self.get_users("https://api.monday.com/v2",
                           {"Authorization": self.credential_id.token})

    def get_boards(self, url, headers):
        """Function for receiving Boards from Monday.com"""
        vals = {}
        response = requests.post(url=url, json={
            'query': '{boards{ name id owner{name} columns {title id type } '
                     'groups{title id} items_page(limit: 100) '
                     '{items {name column_values {id type text } } } } }'},
                                 headers=headers, timeout=10)
        board = self.env['monday.board'].search([]).mapped('board_reference')
        if 'error_code' in response.json().keys():
            raise ValidationError(response.json()['error_message'])
        if 'errors' in response.json().keys():
            raise ValidationError(response.json()['errors'])
        for rec in response.json()['data']['boards']:
            if rec['id'] not in board:
                # Create Board
                board_obj = self.env['monday.board'].create([{
                    'name': rec['name'],
                    'board_reference': rec['id'],
                    'owner': rec['owner']['name']
                }])
            else:
                board_obj = self.env['monday.board'].search([('board_reference',
                                                             '=', rec['id'])])
            for item in rec['groups']:
                board_obj.write({
                    'group_ids': [
                        (0, 0,
                         {'name': item['title'],
                          'group': item['id']}),
                    ]
                })
            for item in rec['items_page']['items']:
                # Update Items
                board_obj.write({
                    'item_ids': [
                        (0, 0,
                         {'name': item['name'],
                          'column_value_ids': [
                              (0, 0,
                               {'title': value['id'],
                                'item_id': value['id'],
                                'text': value['text'],
                                }) for value in item['column_values']
                          ]
                          }), ]})
                if rec['name'] == 'Contacts' and self.import_contact:
                    for value in item['column_values']:
                        vals[value['id']] = value['text']
                    partner = self.env['res.partner'].search([]).mapped(
                        'monday_reference')
                    if vals['contact_email'] not in partner:
                        # Create User
                        self.env['res.partner'].create({
                            'name': item['name'],
                            'phone': vals['contact_phone'],
                            'email': vals['contact_email'],
                            'company_name': vals[
                                'Company'] if 'Company' in vals.keys()
                            else False,
                            'monday_reference': True
                        })

    def get_users(self, apiurl, headers):
        """Function for receiving Users from Monday.com"""
        response = requests.post(url=apiurl,
                                 json={'query': '{users { id name email }}'},
                                 headers=headers, timeout=10)
        if 'error_code' in response.json().keys():
            raise ValidationError(response.json()['error_message'])
        if 'errors' in response.json().keys():
            raise ValidationError(response.json()['errors'])
        for rec in response.json()['data']['users']:
            if not self.env['res.users'].search([('login', '=', rec['email'])]):
                self.env['res.users'].create({
                    'name': rec['name'],
                    'email': rec['email'],
                    'login': rec['email'],
                    'password': 'demo_password',
                    'monday_reference': rec['id']
                })
