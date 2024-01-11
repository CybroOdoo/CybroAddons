# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
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
                                help='Zoom meeting join Rrl')
    zoom_meet_code = fields.Char(string='Zoom Meet Code',
                                 help='Joining meeting code')
    zoom_event = fields.Char(string='Zoom Event ID',
                             help='Event ID of the Zoom meet')
    description = fields.Text('Description',
                              states={'done': [('readonly', True)]},
                              compute="_compute_description", store=True,
                              help='Description regarding the meeting')

    @api.depends('zoom_meet_code', 'zoom_meet_url')
    def _compute_description(self):
        for rec in self:
            if rec.zoom_meet_code and rec.zoom_meet_url:
                rec.description = ("Join the Zoom Meeting at "
                                   + str(rec.zoom_meet_url) +
                                   "using the Meeting code " +
                                   str(rec.zoom_meet_code))

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

    @api.onchange("is_zoom_meet")
    def _onchange_is_zoom_meet(self):
        """Delete a meeting from Zoom"""
        if not self.is_zoom_meet and self.zoom_event:
            header = {
                'Authorization':
                    'Bearer %s' % self.env['res.users'].browse(
                        self._context.get(
                            'uid')).company_id.zoom_company_access_token,
                'Content-Type': 'application/json'}
            response = requests.delete(
                'https://api.zoom.us/v2/meetings/%s' % self.zoom_event,
                headers=header)
            if response.status_code == 401:
                raise UserError(_("Token expired, Please refresh token"))
            self.zoom_meet_url = ''
            self.zoom_meet_code = ''
            self.zoom_event = ''

    def action_zoom_meet_url(self):
        """Join Zoom meeting from Odoo"""
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': self.zoom_meet_url,
        }

    def _create_zoom_meet(self, event):
        """Method for creating Zoom meeting"""
        timezone = self._context.get(
            'tz') or self.env.user.partner_id.tz or 'UTC'
        self_tz = self.with_context(tz=timezone)
        payload = json.dumps({
            "start_time": fields.Datetime.context_timestamp(self_tz,
                                                                  fields.Datetime.from_string(event.start)).isoformat(),
            "timezone": self._context.get('tz') or self.env.user.partner_id.tz or 'UTC',
            "topic": event.name,
            "duration": int(event.duration * 60)
        })
        headers = {
            'Authorization': 'Bearer %s' % self.env['res.users'].browse(
                self._context.get('uid')).company_id.zoom_company_access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.request(
            "POST", "https://api.zoom.us/v2/users/me/meetings",
            headers=headers, data=payload)
        if response.json().get('code') == 124:
            raise UserError(_("Token expired. Please refresh the token"))
        if response.json().get('start_url'):
            event.zoom_event = response.json()['id']
            event.zoom_meet_url = response.json()['join_url']
            event.zoom_meet_code = response.json()['id']
        else:
            raise ValidationError(response.json()['message'])

    def unlink(self):
        """Delete Zoom meet with unlink method"""
        for event in self:
            if event.is_zoom_meet and event.zoom_event:
                header = {
                    'Authorization':
                        'Bearer %s' % self.env['res.users'].browse(
                            self._context.get(
                                'uid')).company_id.zoom_company_access_token,
                    'Content-Type': 'application/json'}
                response = requests.delete(
                    'https://api.zoom.us/v2/meetings/%s' % event.zoom_event,
                    headers=header)
                if response.status_code == 401:
                    raise UserError(_("Token Expired, please refresh token"))
        return super().unlink()
