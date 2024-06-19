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
import json
import requests
from datetime import datetime, time
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ImportExportTicket(models.TransientModel):
    """This class is used to import and export the tickets between odoo and
    zendesk"""
    _name = 'import.export.ticket'
    _description = 'Import and Export Tickets'
    _inherit = 'mail.thread'

    start_date = fields.Date(string='Start Date',
                             help='Mention the start date', Required=True)
    end_date = fields.Date(string='End Date', help='Mention the end date',
                           Required=True)

    @api.constrains('start_date', 'end_date')
    def check_start_date(self):
        """This function is used to validate the entered date"""
        if not self.start_date or not self.end_date:
            raise ValidationError(_("Please provide the dates"))
        if self.start_date > self.end_date:
            raise ValidationError(_("Please check the date that you "
                                    "provide"))

    def action_import_tickets(self):
        """This function is used to import the tickets from Zendesk"""
        company_domain = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_zendesk_connector.company_domain')
        company_email = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_zendesk_connector.company_email')
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_zendesk_connector.api_key')
        # Url for getting the tickets
        url = f"https://{company_domain}.zendesk.com/api/v2/tickets.json"
        headers = {
            "Content-Type": "application/json",
        }
        auth = (f"{company_email}/token", api_key)
        response = requests.get(url, headers=headers, auth=auth)
        if response.ok:
            tickets = response.json()["tickets"]
            for ticket in tickets:
                zendesk_ticket_date = datetime.strptime(
                    ticket["created_at"],
                    '%Y-%m-%dT%H:%M:%SZ').date()
                if self.start_date <= zendesk_ticket_date <= self.end_date:
                    exist_ticket = self.env['help.ticket'].search(
                        [('zendesk_ticket_no', '=', ticket["id"])])
                    if not exist_ticket:
                        requester_id = ticket["requester_id"]
                        # Url for getting each requester
                        requester_url = f'https://{company_domain}.zendesk.com/api/v2/users/{requester_id}.json'
                        requester_response = requests.get(requester_url,
                                                          headers=headers,
                                                          auth=auth,
                                                          timeout=60)
                        # customer=0
                        if response.status_code == 200:
                            requester_data = requester_response.json()['user']
                            requester_name = requester_data['name']
                            requester_email = requester_data['email']
                            customer = self.env['res.partner'].search(
                                [('name', '=', requester_name),
                                 ('email', '=', requester_email)]).id
                            if not customer:
                                new_customer = self.env['res.partner'].create({
                                    'name': requester_name,
                                    'email': requester_email
                                })
                                customer = new_customer.id
                            else:
                                pass
                            priority_field = {
                                None: '0',
                                'low': '1',
                                'normal': '2',
                                'high': '3',
                                'urgent': '4'
                            }
                            priority = priority_field.get(ticket["priority"],
                                                          '0')
                            self.env['help.ticket'].create({
                                "subject": ticket["subject"],
                                "description": ticket["description"],
                                'priority': priority,
                                'is_ticket_from_zendesk': True,
                                'zendesk_ticket_no': ticket["id"],
                                'customer_id': customer,
                                'email': requester_email,
                            })
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Success!"),
                    'message': _("Tickets are imported"
                                 " successfully"),
                    'sticky': False,
                }
            }
        else:
            # Error in Importing tickets
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Error!"),
                    'message': _(
                        "It seems to have some issue with importing "
                        "the tickets"),
                    'sticky': False,
                }
            }
        return notification

    def action_export_tickets(self):
        """This function is used to export tickets from odoo to zendesk"""
        company_domain = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_zendesk_connector.company_domain')
        company_email = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_zendesk_connector.company_email')
        password = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_zendesk_connector.password')
        export_start_date = datetime.combine(self.start_date, time.min)
        export_end_date = datetime.combine(self.end_date, time.min)
        headers = {'content-type': 'application/json'}
        tickets_rec = self.env['help.ticket'].search(
            [('create_date', '>=', export_start_date),
             ('create_date', '<=', export_end_date),
             ('is_ticket_from_zendesk', '=', False),
             ])
        for rec in tickets_rec:
            # Url to check whether a Zendesk ticket with same id exist
            zen_id_search_url = f'https://{company_domain}.zendesk.com/api/v2/tickets/{rec.zendesk_ticket_no}.json'
            zen_id_search_response = requests.get(zen_id_search_url, auth=(
                company_email, password))
            if zen_id_search_response.status_code != 200:
                # Ticket with same id  does not exit, so create it as
                # a new ticket in Zendesk
                # Synchronizing the priority of Zendesk with priority of Odoo
                priority = {
                    '1': 'low',
                    '2': 'normal',
                    '3': 'high',
                    '4': 'urgent'
                }
                zen_prio = 'None'
                if rec.priority in priority:
                    zen_prio = priority[rec.priority]
                # With this url checking whether a customer with same email
                # is existing in Zendesk
                customer_search_url = f'https://{company_domain}.zendesk.com/api/v2/users/search.json?query=email:{rec.email}'
                search_response = requests.get(customer_search_url,
                                               auth=(company_email, password))
                if search_response.status_code == 200:
                    results = search_response.json().get('users')
                    if results and len(results) > 0:
                        # Customer Exist
                        customer_id = results[0]['id']

                    else:
                        # Customer does not exist so, need to create a new
                        # customer
                        data = {
                            'user': {
                                'name': rec.customer_id.name,
                                'email': rec.email,
                            }
                        }
                        # Creating new user
                        user_url = f'https://{company_domain}.zendesk.com/api/v2/users.json'
                        user_response = requests.post(user_url, json=data,
                                                      auth=(
                                                          company_email,
                                                          password),
                                                      headers=headers)
                        if user_response.status_code == 201:
                            # User created successfully, get new ID
                            customer_id = user_response.json().get('user').get(
                                'id')
                        else:
                            raise UserError(_(user_response.json()['error']))
                # Creating a new ticket to Zendesk from Odoo
                data = {
                    'ticket': {'subject': rec.subject, 'priority': zen_prio,
                               'comment': {'body': rec.description},
                               'requester_id': customer_id}}
                url = f'https://{company_domain}.zendesk.com/api/v2/tickets.json'
                response = requests.post(url, data=json.dumps(data),
                                         auth=(company_email, password),
                                         headers=headers)
                if response.status_code != 201:
                    # Problem with exporting ticket to Zendesk
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _("Error!"),
                            'message': _("Problem with exporting ticket to"
                                         " Zendesk"),
                            'sticky': False,
                        }
                    }
                # Exported the tickets Successfully
                if response.json().get("ticket"):
                    rec.zendesk_ticket_no = response.json()['ticket']['id']
