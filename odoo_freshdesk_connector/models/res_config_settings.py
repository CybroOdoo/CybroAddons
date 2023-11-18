# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S(odoo@cybrosys.com)
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
import base64
import json
import requests
from requests import RequestException
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """
    Inherits the model Res Config Settings to extend and add the fields and
    methods
    """
    _inherit = 'res.config.settings'

    domain = fields.Char(string='Domain',
                         help='Enter the domain of the freshdesk of the user',
                         config_parameter='odoo_freshdesk_connector.domain')
    api_key = fields.Char(string='API Key',
                          help='Enter the API key to connect to the freshdesk',
                          config_parameter='odoo_freshdesk_connector.api_key')
    import_contacts = fields.Boolean(string='Import Contacts',
                                     help='Make true if you want to import '
                                          'contacts',
                                     config_parameter='odoo_freshdesk_connector.import_contacts')
    import_tickets = fields.Boolean(string='Import Tickets',
                                    help='Make true if you want to import '
                                         'tickets',
                                    config_parameter='odoo_freshdesk_connector.import_tickets')
    export_tickets = fields.Boolean(string='Export Tickets',
                                    help='Make true if you want to export '
                                         'tickets',
                                    config_parameter='odoo_freshdesk_connector.export_tickets')

    @api.onchange('import_contacts')
    def _onchange_import_contacts(self):
        """
        Summary:
            This is the method _onchange_import_contacts which is here used to
            make the import_tickets booleans if the import_contacts boolean is
            True
        """
        if self.import_contacts:
            self.import_tickets = True

    @api.onchange('import_tickets')
    def _onchange_import_tickets(self):
        """
        Summary:
            This is the method _onchange_import_tickets which is triggered on
            the change of the field import_tickets to change the import_contacts
            boolean to false if the import_tickets boolean is False
        """
        if self.import_contacts and not self.import_tickets:
            self.import_contacts = False

    def action_test_freshdesk_connection(self):
        """
        Summary:
            This is the method action_test_freshdesk_connection which is
            triggered when clicked on the test, which checks whether we can
            connect to the freshdesk with the given credentials as API key and
            the domain.
        Returns:
            notification: The notification which returns the notification if
            whether the connection to the freshdesk in successful or not.
        """
        if self.api_key and self.domain:
            api_key_base64 = base64.b64encode(self.api_key.encode()).decode()
            url = self.domain + '/api/v2/tickets'
            payload = {}
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {api_key_base64}',
            }
            try:
                response = requests.request("GET", url, headers=headers,
                                            data=payload, timeout=10)
                return self.action_notify(
                    True) if response.status_code == 200 else self.action_notify(
                    False)
            except RequestException as exception:
                raise ValidationError(_('Invalid domain')) from exception
        else:
            raise ValidationError(_('Please enter the credentials'))

    def action_notify(self, success):
        """
        Summary:
            This is the method action_notify which is triggered from the method
            action_test_freshdesk_connection to create the notification whether
            the connection is successful or not.
        Args:
            success: True if the connection to the freshdesk is successful
            else False
        Returns:
            notification: which returns the client action to show the
            notification as successful or not to the method
            action_test_freshdesk_connection
        """
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connection successful!') if success is True else _(
                    'Connection not successful!'),
                'message': 'Connection to Freshdesk is successful.' if success is True else 'Connection to Freshdesk is not successful.',
                'sticky': True,
                'type': 'success' if success is True else 'danger'
            }
        }
        return notification

    def action_execute_freshdesk_operation(self):
        """
        Summary:
            This is the method action_execute_freshdesk_operation which is
            triggered when the button to execute the operations of importing
            and exporting the data from the Freshdesk is clicked from section
            of the freshdesk from the general settings.
        """
        imported_tickets = 0
        exported_tickets = 0
        if self.import_tickets:
            imported_tickets = self.action_import_tickets()
        if self.export_tickets:
            exported_tickets = self.action_export_tickets()
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(
                    'Executed the operation successfully!'),
                'message': f'Successfully imported {imported_tickets} Tickets '
                           f'and exported {exported_tickets} tickets',
                'sticky': True,
                'type': 'success'
            }
        }
        return notification

    def action_import_tickets(self):
        """
        Summary:
            This is the method create_tickets which is triggered from the method
            action_execute_freshdesk_operation if the import_tickets boolean is
            true from the record when executing the operation.
        """
        if self.api_key and self.domain:
            api_key_base64 = base64.b64encode(self.api_key.encode()).decode()
            ticket_url = self.domain + '/api/v2/tickets?include=description'
            payload = {}
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {api_key_base64}',
            }
            try:
                tickets_response = requests.request("GET", ticket_url,
                                                    headers=headers,
                                                    data=payload, timeout=10)
                tickets_data = json.loads(tickets_response.text)
                tickets_count = 0
                for ticket in tickets_data:
                    existing_ticket = self.env['help.ticket'].search(
                        [('freshdesk_id', '=', ticket.get('id'))], limit=1)
                    if not existing_ticket:
                        ticket_vals = {
                            'subject': ticket.get('subject'),
                            'description': ticket.get('description'),
                            'freshdesk_id': ticket.get('id'),
                        }
                        if self.import_contacts:
                            contact = self.action_import_contact(ticket=ticket,
                                                                 headers=headers,
                                                                 payload=payload)
                            ticket_vals['customer_id'] = contact.id
                        self.env['help.ticket'].create(ticket_vals)
                        tickets_count += 1
                return tickets_count
            except RequestException as exception:
                raise ValidationError(
                    _('Invalid domain')) from exception
        else:
            raise ValidationError(_('Please enter the credentials'))

    def action_import_contact(self, ticket, headers, payload):
        """
        Summary:
            This is the method create_contact which is called from the method
            create_tickets, which is here used to create the contact for the
            corresponding ticket and add to that ticket if the boolean import
            contact is true in the configuration of the freshdesk
        Args:
            ticket: The ticket which gets the contact id
            headers: Headers needed for the request to get data of the contact
            payload: The payload for the contact request
        Returns:
            contact: Checks if there is already any contact present with this
                id which means that is already imported if not then a new
                contact will be created and returned to the parent method.
            existing_contact: Returns the existing contact if there is already
                a contact with this freshdesk id.
        """
        contact_url = self.domain + '/api/v2/contacts/' + str(
            ticket.get('requester_id'))
        contact_response = requests.request("GET", contact_url,
                                            headers=headers,
                                            data=payload, timeout=10)
        contacts_data = json.loads(contact_response.text)
        existing_contact = self.env['res.partner'].search(
            [('freshdesk_id', '=', contacts_data.get('id'))], limit=1)
        if not existing_contact:
            contact = self.env['res.partner'].create({
                'name': contacts_data.get('name'),
                'email': contacts_data.get('email'),
                'freshdesk_id': contacts_data.get('id'),
                'phone': contacts_data.get('phone'),
            })
            return contact
        return existing_contact

    def action_export_tickets(self):
        """
        Summary:
            This is the method action_export_tickets which is called from the
            method action_execute_freshdesk_operation, this method acts the
            method to export the tickets to the freshdesk that is already not
            exported
        """
        tickets_link = self.domain + '/api/v2/tickets'
        api_key_base64 = base64.b64encode(self.api_key.encode()).decode()
        ticket_count = 0
        for ticket in self.env['help.ticket'].search([]).filtered(
                lambda x: not x.freshdesk_id):
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {api_key_base64}'
            }
            contact = self.action_export_contact(ticket=ticket, header=headers)
            payload = json.dumps({
                "subject": ticket.subject,
                "description": ticket.description,
                "email": ticket.customer_id.email if ticket.customer_id else None,
                "priority": int(ticket.priority),
                'requester_id': int(contact),
                'status': ticket.stage_id.id,
            })
            try:
                ticket_response = requests.post(tickets_link, headers=headers,
                                                data=payload, timeout=10)
                ticket_data = json.loads(ticket_response.text)
                ticket.freshdesk_id = ticket_data.get('id')
                ticket_count += 1
            except RequestException as exception:
                raise ValidationError(_('Invalid domain')) from exception
        return ticket_count

    def action_export_contact(self, ticket, header):
        """
        Summary:
            This is the method export_contact which is called from the method
            action_export_tickets, which is here used to create the contact
            which is present in the customer that is not imported or exported
            already.
        Args:
            ticket: Record of the ticket that is present in the model that
            should be exported.
        Returns:
            contact: Create contact id or if the user already has the id ie,
            already imported then that already existing freshdesk id will be
            returned
            existing_contact: Returns the existing contact is the contact with
            this freshdesk id is already imported or existing
        """
        if not ticket.customer_id.freshdesk_id:
            contact_link = self.domain + '/api/v2/contacts'
            payload = json.dumps({
                "name": ticket.customer_id.name,
                "email": ticket.customer_id.email,
                "active": True,
                "address": ticket.customer_id.contact_address,
                "phone": ticket.customer_id.phone,
            })
            create_response = requests.post(contact_link, headers=header,
                                            data=payload, timeout=10)
            contacts_data = json.loads(create_response.text)
            contact = contacts_data.get('id')
            ticket.customer_id.freshdesk_id = contact
            return contact
        existing_contact = ticket.customer_id.freshdesk_id
        return existing_contact
