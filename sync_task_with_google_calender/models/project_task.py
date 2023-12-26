# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    """ Extend 'project.task' model to add Google Calendar integration."""
    _inherit = 'project.task'

    is_add_in_gcalendar = fields.Boolean(string="Add In G-Calendar Event",
                                         help="Set this field  True if you want to"
                                              " add this task to Google Calendar.")
    task_event = fields.Char(string="Task Google Calendar Event ID",
                             help="This field stores the unique ID of Google"
                                  " Calendar event associated with the task.")
    task_created = fields.Char(string="Task Creator ID",
                               help="This field stores the unique ID of the "
                                    "task creator or owner.")

    @api.model
    def create(self, vals):
        """Override create() method to sync task to Google Calendar if
        enabled."""
        task = super().create(vals)
        if task.is_add_in_gcalendar:
            self.sync_task_to_google_calendar(task)
        return task

    def write(self, vals):
        """Override write() method to update Google Calendar event if relevant
        fields are modified."""
        res = super().write(vals)
        if any(field in ['user_id', 'partner_id', 'name', 'description',
                         'date_deadline', 'due_date', 'is_add_in_gcalendar'] for
               field in vals):
            task = self
            self.update_google_calendar_event(task)
        return res

    def sync_task_to_google_calendar(self, task):
        """Sync the task to Google Calendar by creating a new event."""
        if self.is_add_in_gcalendar and (
                not self.partner_id or not self.date_deadline):
            required_fields = []
            if not self.partner_id:
                required_fields.append(self._fields['partner_id'].string)
            if not self.date_deadline:
                required_fields.append(self._fields['date_deadline'].string)
            raise UserError(_(
                f"The following fields are required when 'Add In G-Calendar"
                f" Event' is enabled: {', '.join(required_fields)}"))
        headers, url = self._prepare_headers_and_url(
            self.env.user.google_user_mail)
        project_name = task.project_id.name.capitalize() if task.project_id \
            else ''
        event = {
            'summary': f"Project: {project_name} - Task: {task.name}",
            'description': task.description,
            'start': {'date': str(task.date_deadline)},
            'end': {
                'date': str(task.date_deadline)} if task.date_deadline else {
                'date': ''},
            'extendedProperties': {
                'private': {
                    'create_date_time': str(task.create_date),
                    'user': task.manager_id.name if task.manager_id else '',
                }
            },
            'attendees': [{'email': attendee.email} for attendee in
                          task.user_ids if attendee.email],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 0},
                    {'method': 'email', 'minutes': 24 * 60},
                ]
            }
        }
        if task.partner_id and task.partner_id.email:
            event['attendees'].append({'email': task.partner_id.email})
            event['reminders']['overrides'].append(
                {'method': 'email', 'minutes': 60})
        response = requests.post(url, headers=headers, json=event)
        if response.status_code == 200:
            event_id = response.json().get('id')
            creator_email = response.json().get('creator', {}).get('email')
            message = f'Google Calendar Event created\nTask ID: {task.id}\n' \
                      f'Event ID: {event_id}\nCreator Email: {creator_email}'
            task.message_post(body=message)
            task.task_event = event_id
            task.task_created = creator_email
        else:
            message = 'Failed to create event in Google Calendar'
            task.message_post(body=message)

    def update_google_calendar_event(self, task):
        """Update the Google Calendar event associated with the task."""
        event_id = task.task_event
        if not event_id:
            self.sync_task_to_google_calendar(task)
            return
        event = {
            'summary': task.name,
            'description': task.description,
            'start': {'date': str(task.date_deadline)},
            'end': {
                'date': str(task.date_deadline)} if task.date_deadline else {
                'date': ''},
            'extendedProperties': {
                'private': {
                    'create_date_time': str(task.create_date),
                    'user': task.manager_id.name if task.manager_id else '',
                }
            },
            'attendees': [{'email': attendee.email} for attendee in
                          task.user_ids if attendee.email],
        }
        headers, url = self._prepare_headers_and_url(
            self.env.user.google_user_mail, event_id)
        response = requests.patch(url, headers=headers, json=event)
        if response.status_code == 200:
            message = f'Event updated in Google Calendar'
            task.message_post(body=message)
        else:
            message = f'Failed to update event in Google Calendar'
            task.message_post(body=message)

    def _prepare_headers_and_url(self, google_calendar_id, event_id=None):
        """
        Prepare headers and URL for Google Calendar API requests.
        """
        headers = {
            "Authorization": f"Bearer {self.env.user.user_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        api_key = self.env.user.api_key
        url = f"https://www.googleapis.com/calendar/v3/calendars/" \
              f"{google_calendar_id}/events"
        if event_id:
            url += f"/{event_id}"
        url += f"?key={api_key}"
        return headers, url

    def unlink(self):
        """Override unlink method to delete associated Google Calendar
         events."""
        self.delete_google_calendar_events()
        return super(ProjectTask, self).unlink()

    def delete_google_calendar_events(self):
        """Delete associated events from Google Calendar."""
        event_ids = self.mapped('task_event')
        if event_ids:
            headers = {
                "Authorization": f"Bearer {self.env.user.user_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            for event_id in event_ids:
                url = f"https://www.googleapis.com/calendar/v3/calendars/" \
                      f"{self.env.user.google_user_mail}/events/{event_id}" \
                      f"?key=" \
                      f"{self.env.user.api_key}"
                # Delete event from Google Calendar
                response = requests.delete(url, headers=headers)
                return response
