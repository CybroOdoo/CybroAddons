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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError

from .zendesk_api import ODOO_TO_ZENDESK_PRIORITY


class TicketHelpdesk(models.Model):
    """Create, update and delete tickets in Zendesk"""
    _inherit = 'ticket.helpdesk'

    zendesk_ticket_no = fields.Char(string='Zendesk Ticket Id',
                                    help='Shows the Id of ticket in Zendesk',
                                    readonly=True, copy=False)
    is_ticket_from_zendesk = fields.Boolean(string='Ticket From Zendesk',
                                            help='Is this a ticket from'
                                                 ' Zendesk', copy=False)

    def _prepare_zendesk_ticket_vals(self, requester_id):
        """Payload for creating/updating a ticket in Zendesk"""
        self.ensure_one()
        vals = {
            'subject': self.subject,
            # None = no priority in Zendesk (the string 'None' is rejected)
            'priority': ODOO_TO_ZENDESK_PRIORITY.get(self.priority),
            'requester_id': requester_id,
        }
        if self.description:
            vals['comment'] = {'body': self.description}
        return vals

    def action_create_to_zendesk(self):
        """Create this ticket in Zendesk"""
        self.ensure_one()
        zendesk = self.env['zendesk.api']
        if not zendesk._is_connected():
            return zendesk.notify(
                _("Warning"),
                _("Zendesk connection is disabled. Please enable 'Connect "
                  "Zendesk' in settings."), 'warning')
        if self.zendesk_ticket_no:
            return zendesk.notify(_("Warning"), _("Ticket already exists"),
                                  'warning')
        try:
            requester_id = zendesk._find_or_create_user(
                self.customer_id.name, self.email)
            result = zendesk._request('POST', 'tickets.json', json={
                'ticket': self._prepare_zendesk_ticket_vals(requester_id)})
        except UserError as error:
            return zendesk.notify(
                _("Error!"),
                _("Creation of Zendesk ticket failed: %s", error), 'danger')
        self.zendesk_ticket_no = str(result['ticket']['id'])
        return zendesk.notify(_("Success!"),
                              _("Successfully Created the ticket in Zendesk"),
                              'success')

    def action_update_zendesk_ticket(self):
        """Update the linked Zendesk ticket from Odoo"""
        self.ensure_one()
        zendesk = self.env['zendesk.api']
        if not zendesk._is_connected():
            return zendesk.notify(
                _("Warning"),
                _("Zendesk connection is disabled. Please enable 'Connect "
                  "Zendesk' in settings."), 'warning')
        if not self.zendesk_ticket_no:
            return zendesk.notify(
                _("Warning"),
                _("This ticket is not linked to Zendesk yet. Use 'Create to "
                  "Zendesk' first."), 'warning')
        try:
            requester_id = zendesk._find_or_create_user(
                self.customer_id.name, self.email)
            zendesk._request(
                'PUT', f'tickets/{self.zendesk_ticket_no}.json',
                json={'ticket': self._prepare_zendesk_ticket_vals(
                    requester_id)})
        except UserError as error:
            return zendesk.notify(
                _("Error!"),
                _("Updating the ticket failed: %s", error), 'danger')
        return zendesk.notify(_("Success!"), _("Successfully Updated the "
                                              "ticket"), 'success')

    def action_delete_zendesk_ticket(self):
        """Delete the linked ticket from Zendesk"""
        self.ensure_one()
        zendesk = self.env['zendesk.api']
        if not zendesk._is_connected():
            return zendesk.notify(
                _("Warning"),
                _("Zendesk connection is disabled. Please enable 'Connect "
                  "Zendesk' in settings."), 'warning')
        if not self.zendesk_ticket_no:
            return zendesk.notify(_("Warning"),
                                  _("This ticket is not linked to Zendesk."),
                                  'warning')
        response = zendesk._raw_request(
            'DELETE', f'tickets/{self.zendesk_ticket_no}.json', timeout=180)
        if response.status_code in (204, 404):
            # 404 = already gone in Zendesk; unlink it in Odoo as well
            self.write({'zendesk_ticket_no': False,
                        'is_ticket_from_zendesk': False})
            return zendesk.notify(_("Success!"),
                                  _("Successfully deleted the ticket"),
                                  'success')
        return zendesk.notify(
            _("Error"),
            _("Have issues with deleting the ticket: %s",
              zendesk._error_text(response)), 'danger')
