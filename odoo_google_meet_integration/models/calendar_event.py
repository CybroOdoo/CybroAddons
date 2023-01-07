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
import logging
import random
import json
import requests
import pytz
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo.exceptions import ValidationError, UserError

TIMEOUT = 20
logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    is_google_meet = fields.Boolean('Google Meet', default=False)
    google_meet_url = fields.Char('Google Meet URL',
                                  help='Joinging Meeting URL')
    google_meet_code = fields.Char('Google Meet Code',
                                   help='Joining Meeting Code')
    google_event_id = fields.Char('Google Event ID',
                                  help='Event ID of the google meet')

    def action_google_meet_url(self):
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
    def create(self, vals):
        events = super(CalendarEvent, self).create(vals)
        for event in events:
            if event.is_google_meet:
                self._create_google_meet(event)
        return events

    def write(self, vals):
        events = super(CalendarEvent, self).write(vals)
        for event in self:
            if event.is_google_meet:
                if not event.google_event_id:
                    self._create_google_meet(event)
        return events

    def _create_google_meet(self, cal_event):
        """Creating an event from google calendar"""
        start_dt = fields.Datetime.now()
        finish_dt = fields.Datetime.now().replace(tzinfo=pytz.timezone('UTC'))
        end_date_user = finish_dt.astimezone(pytz.timezone(
            self.env.user.tz or 'UTC')).replace(tzinfo=None)
        difference = relativedelta(end_date_user, start_dt)
        diff_hrs = difference.hours
        diff_min = difference.minutes
        start = cal_event.start
        stop = cal_event.stop
        start_dt = start + timedelta(hours=diff_hrs, minutes=diff_min)
        start_date = start_dt.isoformat()
        stop_dt = stop + timedelta(hours=diff_hrs, minutes=diff_min)
        stop_date = stop_dt.isoformat()
        current_uid = self._context.get('uid')
        user_id = self.env['res.users'].browse(current_uid)
        company_id = user_id.company_id
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        request_id = ''.join(
            random.SystemRandom().choice(chars) for _ in range(16))
        url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1&sendNotifications=True'

        header = {
            'Authorization':
                'Bearer %s' % company_id.hangout_company_access_token,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        event = {
            'summary': cal_event.name,
            'location': cal_event.location or None,
            'description': cal_event.description,
            'conferenceDataVersion': 1,
            'start': {
                'dateTime': start_date,
                'timeZone': user_id.tz,
            },
            'end': {
                'dateTime': stop_date,
                'timeZone': user_id.tz,
            },
            'recurrence': [
            ],
            'attendees': [{'email': partner.email} for partner in
                          cal_event.partner_ids],

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
                               data=json.dumps(event)).json()
        if result.get('error'):
            company_id.google_meet_company_refresh_token()
            result = requests.post(url, headers=header, timeout=TIMEOUT,
                                   data=json.dumps(event)).json()
        if result.get('hangoutLink'):
            cal_event.google_event_id = result['id']
            cal_event.google_meet_url = result['hangoutLink']
            cal_event.google_meet_code = result['conferenceData'][
                'conferenceId']
        else:
            raise ValidationError("Failed to create event,"
                                  "Please check your authorization connection.")

    @api.onchange("is_google_meet")
    def _delete_google_meet(self):
        """Delete an event from google calendar"""
        if not self.is_google_meet:
            event_id = self.google_event_id
            if event_id:
                current_uid = self._context.get('uid')
                user_id = self.env['res.users'].browse(current_uid)
                company_id = user_id.company_id
                url = 'https://www.googleapis.com/calendar/v3/calendars/primary' \
                      '/events/%s' % event_id
                header = {
                    'Authorization':
                        'Bearer %s' % company_id.hangout_company_access_token}
                requests.delete(url, headers=header, timeout=TIMEOUT)
                self.google_meet_url = ''
                self.google_meet_code = ''
                self.google_event_id = ''
