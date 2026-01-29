# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana jabin MP (odoo@cybrosys.com)
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
import pytz
import random
import requests
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

TIMEOUT = 20


class CalendarEvent(models.Model):
    """ Model for calendar events with Google Meet integration."""
    _inherit = 'calendar.event'

    is_google_meet = fields.Boolean(string='Google Meet',
                                    help='Specify whether Google Meet is '
                                         'enabled or not.')
    google_meet_url = fields.Char(string='Google Meet URL',
                                  help='Joining Meeting URL')
    google_meet_code = fields.Char(string='Google Meet Code',
                                   help='Joining Meeting Code')
    google_event = fields.Char(string='Google Event ID',
                               help='Event ID of the Google Meet')

    def action_google_meet_url(self):
        """Generate an action to open the Google Meet URL."""
        url = self.google_meet_url if self.google_meet_url \
            else 'https://meet.google.com/'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url,
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to create Google Meet events."""
        events = super(CalendarEvent, self).create(vals_list)
        google_meet_events = events.filtered(
            lambda event: event.is_google_meet)
        self._create_google_meet(google_meet_events)
        return events

    def write(self, vals):
        """Override write method to update Google Meet events."""
        google_meet_events = self.filtered(
            lambda event: event.is_google_meet and not event.google_event)
        result = super(CalendarEvent, google_meet_events).write(vals)
        self._create_google_meet(google_meet_events)
        return result

    def _create_google_meet(self, cal_event):
        for event in cal_event:
            start_dt = fields.Datetime.from_string(event.start)
            finish_dt = start_dt.replace(tzinfo=pytz.timezone('UTC'))
            end_date_user = finish_dt.astimezone(pytz.timezone(
                self.env.user.tz or 'UTC')).replace(tzinfo=None)
            difference = relativedelta(end_date_user, start_dt)
            start_dt_adjusted = start_dt + timedelta(hours=difference.hours,
                                                     minutes=difference.minutes)
            start_date = start_dt_adjusted.isoformat()
            stop_dt_adjusted = start_dt_adjusted + timedelta(
                hours=difference.hours,
                minutes=difference.minutes)
            user_id = self.env['res.users'].browse(self._context.get('uid'))
            company_id = user_id.company_id
            chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
            request_id = ''.join(random.SystemRandom().choice(chars)
                                 for i in range(16))
            url = ('https://www.googleapis.com/calendar/v3/calendars/primary/'
                   'events?conferenceDataVersion=1&sendNotifications=True')
            header = {
                'Authorization': 'Bearer %s' % company_id.company_access_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            event_data = {
                'summary': event.name,
                'location': event.location or None,
                'description': event.description,
                'conferenceDataVersion': 1,
                'start': {
                    'dateTime': start_date,
                    'timeZone': user_id.tz,
                },
                'end': {
                    'dateTime': stop_dt_adjusted.isoformat(),
                    'timeZone': user_id.tz,
                },
                'recurrence': [],
                'attendees': [{'email': partner.email} for partner in
                              event.partner_ids],
                'conferenceData': {
                    "createRequest": {
                        "conferenceSolutionKey": {
                            "type": "hangoutsMeet"
                        },
                        'requestId': request_id
                    }
                },
            }
            result = requests.post(url, headers=header, timeout=TIMEOUT,
                                   data=json.dumps(event_data)).json()
            if result.get('error'):
                company_id.google_meet_company_refresh_token()
                result = requests.post(url, headers=header, timeout=TIMEOUT,
                                       data=json.dumps(event_data)).json()
            if result.get('hangoutLink'):
                event.google_event = result['id']
                event.google_meet_url = result['hangoutLink']
                event.google_meet_code = result['conferenceData'][
                    'conferenceId']
            else:
                raise ValidationError(
                    _("Failed to create event, Please check your authorization"
                      "connection."))

    @api.onchange("is_google_meet")
    def _onchange_is_google_meet(self):
        """Create a Google Meet event."""
        if self.is_google_meet:
            self.is_google_meet = True
            self._create_google_meet(self)
        else:
            self.google_meet_url = ''
            self.google_meet_code = ''
            self.google_event = ''
        if not self.is_google_meet and self.google_event:
            self.is_google_meet = True
            user_id = self.env['res.users'].browse(
                self._context.get('uid'))
            url = 'https://www.googleapis.com/calendar/v3/calendars/' \
                  'primary/events/%s' % self.google_event
            header = {
                'Authorization':
                    'Bearer %s' % user_id.company_id.company_access_token}
            requests.delete(url, headers=header, timeout=TIMEOUT)
            self.google_meet_url = ''
            self.google_meet_code = ''
            self.google_event = ''
