# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
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
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import timedelta

TIMEOUT = 20


class CalendarEvent(models.Model):
    """    Extends the Odoo Calendar Event model to include Google Meet
    integration fields.
    """
    _inherit = 'calendar.event'

    is_google_meet = fields.Boolean('Google Meet', default=False,
                                    help="Boolean field indicating if the "
                                         "event has a Google Meet integration.")
    google_meet_url = fields.Char('Google Meet URL',
                                  help='Meeting URL to join')
    google_meet_code = fields.Char(help='Meeting code to join')
    google_event_id = fields.Char('Google Event ID',
                                  help='Event ID of the Google Meet')

    def action_google_meet_url(self):
        """ Opens the Google Meet URL associated with the event."""
        meet_url = self.google_meet_url
        if meet_url:
            url = self.google_meet_url
        else:
            url = 'https://meet.google.com/'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url,
        }

    @api.model_create_multi
    def create(self, vals_list):
        """ Overrides the create method to handle the creation of Google
        Meet events.
        """
        events = super().create(vals_list)
        for event in events:
            if event.is_google_meet and not event.google_event_id:
                self._create_google_meet(event)
        return events

    def write(self, vals):
        """Overrides the write method to handle updates for Google Meet
        events."""
        res = super().write(vals)
        for event in self:
            if event.is_google_meet:
                if not event.google_event_id:
                    self._create_google_meet(event)
        return res

    def _create_google_meet(self, cal_event):
        """Creating an event from Google calendar"""
        start_dt = fields.Datetime.now()
        finish_dt = fields.Datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        end_date_user = finish_dt.astimezone(pytz.timezone(
            self.env.user.tz or 'UTC')).replace(tzinfo=None)
        difference = relativedelta(end_date_user, start_dt)
        diff_hrs = difference.hours
        diff_min = difference.minutes
        start = cal_event.start or fields.Datetime.now()
        stop = cal_event.stop or (start + timedelta(hours=1))
        start_dt = start + timedelta(hours=diff_hrs, minutes=diff_min)
        start_date = start_dt.isoformat()
        stop_dt = stop + timedelta(hours=diff_hrs, minutes=diff_min)
        stop_date = stop_dt.isoformat()
        current_uid = self.env.context.get('uid')
        user_id = self.env['res.users'].browse(current_uid) if current_uid else self.env.user
        # The Google credentials are restricted to Settings users; read them
        # with sudo so any calendar user can create a meeting.
        company_id = (user_id.company_id or self.env.company).sudo()
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        request_id = ''.join(
            random.SystemRandom().choice(chars) for _ in range(16))
        url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1&sendNotifications=True'

        def _header():
            return {
                'Authorization': 'Bearer %s' % (
                    company_id.hangout_company_access_token or ''),
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        event = {
            'summary': cal_event.name,
            'location': cal_event.location or None,
            'conferenceDataVersion': 1,
            'start': {
                'dateTime': start_date,
                'timeZone': user_id.tz or 'UTC',
            },
            'end': {
                'dateTime': stop_date,
                'timeZone': user_id.tz or 'UTC',
            },
            'attendees': [{'email': partner.email} for partner in
                          cal_event.partner_ids if partner.email],

            'conferenceData': {
                "createRequest": {
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    },
                    'requestId': request_id
                }
            },
        }
        result = requests.post(url, headers=_header(), timeout=TIMEOUT,
                               data=json.dumps(event)).json()
        if result.get('error'):
            company_id.google_meet_company_refresh_token()
            result = requests.post(url, headers=_header(), timeout=TIMEOUT,
                                   data=json.dumps(event)).json()
        if result.get('hangoutLink'):
            cal_event.google_event_id = result['id']
            cal_event.google_meet_url = result['hangoutLink']
            cal_event.google_meet_code = result['conferenceData'][
                'conferenceId']
        else:
            raise ValidationError(self.env._(
                "Failed to create the event. Please check your "
                "authorization connection."))

    @api.onchange('is_google_meet')
    def _onchange_is_google_meet(self):
        """Delete an event from google calendar"""
        if not self.is_google_meet:
            event_id = self.google_event_id
            if event_id:
                current_uid = self.env.context.get('uid')
                user_id = self.env['res.users'].browse(current_uid) if current_uid else self.env.user
                company_id = (user_id.company_id or self.env.company).sudo()
                url = 'https://www.googleapis.com/calendar/v3/calendars/primary' \
                      '/events/%s' % event_id
                header = {
                    'Authorization':
                        'Bearer %s' % (company_id.hangout_company_access_token or '')}
                requests.delete(url, headers=header, timeout=TIMEOUT)
                self.google_meet_url = ''
                self.google_meet_code = ''
                self.google_event_id = ''
