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

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CalendarEvent(models.Model):
    """Inheriting Calendar events to create zoom meetings"""
    _inherit = 'calendar.event'

    is_zoom_meet = fields.Boolean(string='Zoom Meet',
                                  help='Enable, if zoom meeting.')
    zoom_meet_url = fields.Char(string='Zoom Meet URL',
                                help='To joining Meeting URL')
    zoom_meet_code = fields.Char(string='Zoom Meet Code',
                                 help='Joining Meeting Code')
    zoom_event = fields.Char(string='Zoom Event ID',
                             help='Event ID of the zoom meet')
    videocall_location = fields.Char('Meeting URL', related='zoom_meet_url')
    description = fields.Text('Description',
                              states={'done': [('readonly', True)]},
                              compute="_compute_description", store=True)

    @api.depends('zoom_meet_code', 'zoom_meet_url')
    def _compute_description(self):
        for rec in self:
            if rec.zoom_meet_code and rec.zoom_meet_url:
                rec.description = "Join the Zoom Meeting at " + str(rec.zoom_meet_url) + "using the Meeting Code " + str(rec.zoom_meet_code)

    def action_zoom_meet_url(self):
        """Join zoom from Odoo"""
        meet_url = self.zoom_meet_url
        if meet_url:
            url = self.zoom_meet_url
        else:
            url = 'https://api.zoom.us/v2/'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url,
        }

    @api.model_create_multi
    def create(self, vals):
        """Supering for creating Zoom meetings"""
        events = super(CalendarEvent, self).create(vals)
        for event in events:
            if event.is_zoom_meet:
                self._create_zoom_meet(event)
        return events

    def write(self, vals):
        """Supering for enabling zoom meetings while editing"""
        events = super(CalendarEvent, self).write(vals)
        for event in self:
            if event.is_zoom_meet:
                if not event.zoom_event:
                    self._create_zoom_meet(event)
        return events

    def _create_zoom_meet(self, cal_event):
        """Creating Zoom meeting from odoo in Zoom"""
        url = "https://api.zoom.us/v2/users/me/meetings"
        current_uid = self._context.get('uid')
        user_id = self.env['res.users'].browse(current_uid)
        company_id = user_id.company_id
        duration = cal_event.duration * 60
        payload = json.dumps({
            "start_time": cal_event.start.isoformat(),
            "timezone": 'UTC',
            "topic": cal_event.name,
            "duration": int(duration),
            "settings": {
                "email_notification": False,
                "registrants_confirmation_email": False,
                "registrants_email_notification": False,
                "waiting_room": True,
                "join_before_host": True,
                "mute_participants_upon_entry": True
            }
        })
        headers = {
            'Authorization': 'Bearer %s' % company_id.zoom_company_access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.json().get('code') == 124:
            raise UserError(_("Token Expired, please refresh token"))
        if response.json().get('start_url'):
            cal_event.zoom_event = response.json()['id']
            cal_event.zoom_meet_url = response.json()['join_url']
            cal_event.zoom_meet_code = response.json()['id']
        else:
            raise ValidationError("Failed to create Zoom event,"
                                  "Please check your authorization connection.")

    @api.onchange("is_zoom_meet")
    def _onchange_is_zoom_meet(self):
        """Delete a meeting from zoom """
        if not self.is_zoom_meet:
            event_id = self.zoom_event
            if event_id:
                current_uid = self._context.get('uid')
                user_id = self.env['res.users'].browse(current_uid)
                company_id = user_id.company_id
                url = 'https://api.zoom.us/v2/meetings/%s' % event_id
                header = {
                    'Authorization':
                        'Bearer %s' % company_id.zoom_company_access_token,
                    'Content-Type': 'application/json'}
                response = requests.delete(url, headers=header)
                if response.status_code == 401:
                    raise UserError(_("Token Expired, please refresh token"))
                self.zoom_meet_url = ''
                self.zoom_meet_code = ''
                self.zoom_event = ''

    def unlink(self):
        """Delete Zoom meet with unlink method"""
        for event in self:
            if event.is_zoom_meet and event.zoom_event:
                current_uid = self._context.get('uid')
                user_id = self.env['res.users'].browse(current_uid)
                company_id = user_id.company_id
                url = 'https://api.zoom.us/v2/meetings/%s' % event.zoom_event
                header = {
                    'Authorization':
                        'Bearer %s' % company_id.zoom_company_access_token,
                    'Content-Type': 'application/json'}
                response = requests.delete(url, headers=header)
                if response.status_code == 401:
                    raise UserError(_("Token Expired, please refresh token"))
        events = super(CalendarEvent, self).unlink()
        return events
