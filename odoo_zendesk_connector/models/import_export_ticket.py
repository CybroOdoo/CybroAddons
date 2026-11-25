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
from datetime import datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .zendesk_api import ZENDESK_TO_ODOO_PRIORITY


class ImportExportTicket(models.TransientModel):
    """Import and export tickets between Odoo and Zendesk"""
    _name = 'import.export.ticket'
    _description = 'Import and Export Tickets'

    start_date = fields.Date(help='Mention the start date', required=True)
    end_date = fields.Date(help='Mention the end date', required=True)

    @api.constrains('start_date', 'end_date')
    def check_start_date(self):
        """Validate the entered dates"""
        for rec in self:
            if not rec.start_date or not rec.end_date:
                raise ValidationError(_("Please provide the dates"))
            if rec.start_date > rec.end_date:
                raise ValidationError(_("Please check the date that you "
                                        "provide"))

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------
    def _fetch_zendesk_tickets(self):
        """All Zendesk tickets created between start_date and end_date.
        Uses the Search API so only the date range is downloaded, and
        follows next_page so more than 100 tickets are handled."""
        zendesk = self.env['zendesk.api']
        query = (f'type:ticket created>={self.start_date.isoformat()} '
                 f'created<{(self.end_date + timedelta(days=1)).isoformat()}')
        result = zendesk._request('GET', 'search.json',
                                 params={'query': query, 'per_page': 100})
        tickets = list(result.get('results') or [])
        while result.get('next_page'):
            result = zendesk._request('GET', result['next_page'])
            tickets += result.get('results') or []
        return tickets

    def _get_or_create_partner(self, requester_id, user_cache):
        zendesk = self.env['zendesk.api']
        if requester_id and requester_id not in user_cache:
            response = zendesk._raw_request('GET',
                                           f'users/{requester_id}.json')
            zd_user = response.json().get('user', {}) if response.ok else {}
            user_cache[requester_id] = zd_user
        zd_user = user_cache.get(requester_id) or {}
        user_name = (zd_user.get('name') or '').strip()
        user_email = (zd_user.get('email') or '').strip()

        if user_email:
            email = user_email
            partner = self.env['res.partner'].search(
                [('email', '=ilike', email)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': user_name or email,
                    'email': email,
                })
        else:
            # Dedicated partner per requester when email is missing, preventing
            # all unknown requesters from falling back to a single shared partner.
            fallback_name = user_name or (
                _("Zendesk User #%s", requester_id) if requester_id else _("Unknown Requester")
            )
            fallback_email = f"zendesk_user_{requester_id}@example.com" if requester_id else False
            domain = [('name', '=', fallback_name)]
            if fallback_email:
                domain = ['|', ('name', '=', fallback_name), ('email', '=ilike', fallback_email)]
            partner = self.env['res.partner'].search(domain, limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': fallback_name,
                    'email': fallback_email,
                })
            email = partner.email or fallback_email or ''
        return partner, email

    def action_import_tickets(self):
        """Import the tickets from Zendesk, updating existing and creating new"""
        self.ensure_one()
        zendesk = self.env['zendesk.api']
        if not zendesk._is_connected():
            return zendesk.notify(
                _("Warning"),
                _("Zendesk connection is disabled. Please enable 'Connect "
                  "Zendesk' in settings."), 'warning')
        helpdesk = self.env['ticket.helpdesk']
        try:
            tickets = self._fetch_zendesk_tickets()
        except UserError as error:
            return zendesk.notify(
                _("Error!"),
                _("It seems to have some issue with importing the tickets: "
                  "%s", error), 'danger')
        user_cache = {}
        created_count = 0
        updated_count = 0
        for ticket in tickets:
            partner, email = self._get_or_create_partner(
                ticket.get('requester_id'), user_cache)
            ticket_vals = {
                'subject': ticket.get('subject') or _(
                    'Zendesk Ticket #%s', ticket['id']),
                'description': (ticket.get('description') or
                                ticket.get('subject') or
                                _('No description provided')),
                'priority': ZENDESK_TO_ODOO_PRIORITY.get(
                    ticket.get('priority'), '0'),
                'customer_id': partner.id,
                'email': email,
            }
            existing = helpdesk.search(
                [('zendesk_ticket_no', '=', str(ticket['id']))], limit=1)
            if existing:
                existing.write(ticket_vals)
                updated_count += 1
            else:
                ticket_vals.update({
                    'zendesk_ticket_no': str(ticket['id']),
                    'is_ticket_from_zendesk': True,
                })
                helpdesk.create(ticket_vals)
                created_count += 1

        if updated_count:
            message = _(
                "%(created)s ticket(s) imported, %(updated)s ticket(s) updated successfully",
                created=created_count, updated=updated_count)
        else:
            message = _("%s ticket(s) imported successfully", created_count)
        return zendesk.notify(_("Success!"), message, 'success')

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def action_export_tickets(self):
        """Export tickets from Odoo to Zendesk"""
        self.ensure_one()
        zendesk = self.env['zendesk.api']
        if not zendesk._is_connected():
            return zendesk.notify(
                _("Warning"),
                _("Zendesk connection is disabled. Please enable 'Connect "
                  "Zendesk' in settings."), 'warning')
        export_start = datetime.combine(self.start_date, time.min)
        # include the whole end day
        export_end = datetime.combine(self.end_date, time.max)
        tickets = self.env['ticket.helpdesk'].search([
            ('create_date', '>=', export_start),
            ('create_date', '<=', export_end),
            ('is_ticket_from_zendesk', '=', False),
            ('zendesk_ticket_no', '=', False),
        ])
        count = 0
        errors = []
        for rec in tickets:
            try:
                requester_id = zendesk._find_or_create_user(
                    rec.customer_id.name, rec.email)
                result = zendesk._request('POST', 'tickets.json', json={
                    'ticket': rec._prepare_zendesk_ticket_vals(requester_id)})
            except UserError as error:
                errors.append(f'{rec.display_name}: {error}')
                continue
            rec.zendesk_ticket_no = str(result['ticket']['id'])
            count += 1
        if errors:
            return zendesk.notify(
                _("Exported with errors"),
                _("%(count)s ticket(s) exported. Failed:\n%(errors)s",
                  count=count, errors='\n'.join(errors)),
                'warning', sticky=True)
        return zendesk.notify(_("Success!"),
                              _("%s ticket(s) exported successfully", count),
                              'success')
