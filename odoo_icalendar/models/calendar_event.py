# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope it will be useful,
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
from datetime import timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext, is_html_empty

_logger = logging.getLogger(__name__)
try:
    import vobject
except ImportError:
    _logger.warning(
        "`vobject` Python module not found, iCal file generation disabled. "
        "Consider installing this module if you want to generate iCal files")
    vobject = None


class Meeting(models.Model):
    """This class inherits calendar.event model to provide RFC 5545 compliant
    iCalendar generation with Google Calendar support, and mail actions."""
    _inherit = 'calendar.event'

    def _populate_ics_event(self, event):
        """Populate a vobject vevent component from a calendar.event record.
        Ensures RFC 5545 compliance and compatibility with Google Calendar:
        - Stable, unique UID without whitespace
        - Standard UTC DTSTAMP and CREATED
        - Proper VALUE=DATE for all-day events with non-inclusive DTEND
        - UTC timestamps for timed events
        - Negative trigger durations for alarms
        - Formatted ORGANIZER and ATTENDEE entries (excluding organizer from attendees)
        - Clean recurrence rules stripping RRULE prefixes
        """
        self.ensure_one()
        now_utc = fields.Datetime.now().replace(tzinfo=ZoneInfo("UTC"))
        event.add('created').value = (self.create_date or fields.Datetime.now()).replace(
            tzinfo=ZoneInfo("UTC"))
        event.add('dtstamp').value = now_utc

        base_url = self.get_base_url()
        parsed = urlparse(base_url) if base_url else None
        domain = parsed.netloc.split(':')[0] if parsed and parsed.netloc else 'odoo.local'
        if not domain:
            domain = 'odoo.local'
        event.add('uid').value = f"odoo-calendar-{self.id}@{domain}"

        event.add('sequence').value = '0'

        if self.allday:
            start_date = self.start_date or (self.start.date() if self.start else fields.Date.context_today(self))
            stop_date = self.stop_date or (self.stop.date() if self.stop else start_date)
            event.add('dtstart').value = start_date
            event.add('dtend').value = stop_date + timedelta(days=1)
        else:
            if not self.start or not self.stop:
                raise UserError(
                    self.env._(
                        "First you have to specify the date of the invitation for %(name)s.",
                        name=self.name,
                    ),
                )
            event.add('dtstart').value = self.start.replace(tzinfo=ZoneInfo("UTC"))
            event.add('dtend').value = self.stop.replace(tzinfo=ZoneInfo("UTC"))

        event.add('summary').value = self.name or self.env._("Meeting")

        if not is_html_empty(self.description):
            desc_text = html2plaintext(self.description)
            if desc_text:
                event.add('description').value = desc_text

        if self.location:
            event.add('location').value = self.location

        if getattr(self, 'videocall_location', False):
            event.add('url').value = self.videocall_location

        if self.recurrency and self.rrule:
            clean_rrule = self.rrule.splitlines()[-1].replace('RRULE:', '', 1)
            if clean_rrule:
                event.add('rrule').value = clean_rrule

        if self.alarm_ids:
            for alarm in self.alarm_ids:
                valarm = event.add('valarm')
                valarm.add('action').value = 'DISPLAY'
                valarm.add('description').value = alarm.name or 'Odoo'
                interval = alarm.interval
                duration = alarm.duration
                delta = None
                if interval == 'days':
                    delta = timedelta(days=duration)
                elif interval == 'hours':
                    delta = timedelta(hours=duration)
                elif interval == 'minutes':
                    delta = timedelta(minutes=duration)
                if delta is not None:
                    trigger = valarm.add('TRIGGER')
                    trigger.params['related'] = ["START"]
                    trigger.value = -delta

        if self.partner_id and self.partner_id.email:
            organizer = event.add('organizer')
            organizer.value = f"MAILTO:{self.partner_id.email}"
            if self.partner_id.name:
                organizer.params['CN'] = [self.partner_id.display_name.replace('"', "'")]

        for partner in self.partner_ids:
            if partner.email and partner != self.partner_id:
                attendee_add = event.add('attendee')
                attendee_add.value = f"MAILTO:{partner.email}"
                if partner.name:
                    attendee_add.params['CN'] = [partner.display_name.replace('"', "'")]

    def _get_ics_file(self):
        """Returns iCalendar file for the event invitation.
        Overridden to ensure RFC 5545 compliance and Google Calendar compatibility.
        :returns a dict of .ics file bytes for each meeting
        """
        result = {}
        if not vobject:
            return result

        for meeting in self:
            cal = vobject.iCalendar()
            event = cal.add('vevent')
            meeting._populate_ics_event(event)
            result[meeting.id] = cal.serialize().encode('utf-8')

        return result

    def action_send_ics(self):
        """Send mail invitations to attendees with attached ics file."""
        self.ensure_one()
        ics_files = self._get_ics_file()
        ics_data = ics_files.get(self.id)
        if not ics_data:
            raise UserError(self.env._("Could not generate iCalendar file."))

        attachment_values = {
            'name': f"{self.name or 'Event'}.ics",
            'type': 'binary',
            'raw': ics_data,
            'mimetype': 'text/calendar',
            'res_model': 'calendar.event',
            'res_id': self.id,
        }
        attachment = self.env['ir.attachment'].sudo().create(attachment_values)
        email_template = self.env.ref('odoo_icalendar.event_ics_email_template')
        recipient_emails = [attendee.email for attendee in self.partner_ids if attendee.email]
        if not recipient_emails:
            raise UserError(self.env._("There are no attendees with valid email addresses."))
        email_values = {
            'email_to': ', '.join(recipient_emails),
            'attachment_ids': [(4, attachment.id)],
        }
        email_template.send_mail(
            self.id, email_values=email_values, force_send=True)
        email_template.attachment_ids = [(5, 0, 0)]
        return True

    def action_send_attendee_ics_file(self):
        """Send an ics file containing all invited events attached to mail of the attendees."""
        if not vobject:
            return False
        attendee_events = {}
        first_meeting_by_attendee = {}

        for meeting in self:
            for attendee in meeting.partner_ids:
                if not attendee.email:
                    continue
                if attendee.id not in attendee_events:
                    cal = vobject.iCalendar()
                    attendee_events[attendee.id] = cal
                    first_meeting_by_attendee[attendee.id] = meeting
                cal = attendee_events[attendee.id]
                event = cal.add('vevent')
                meeting._populate_ics_event(event)

        if not attendee_events:
            raise UserError(self.env._("None of the attendees have valid email addresses."))

        for attendee_id, cal in attendee_events.items():
            attendee = self.env['res.partner'].browse(attendee_id)
            if not attendee.email:
                continue
            meeting_obj = first_meeting_by_attendee[attendee_id]
            attachment_values = {
                'name': 'All_Events.ics',
                'type': 'binary',
                'raw': cal.serialize().encode('utf-8'),
                'mimetype': 'text/calendar',
                'res_model': 'calendar.event',
                'res_id': meeting_obj.id,
            }
            attachment = self.env['ir.attachment'].sudo().create(attachment_values)
            email_template = self.env.ref(
                'odoo_icalendar.odoo_icalendar_email_template')
            email_values = {
                'email_to': attendee.email,
                'email_cc': False,
                'scheduled_date': False,
                'recipient_ids': [],
                'partner_ids': [],
                'auto_delete': True,
                'attachment_ids': [(4, attachment.id)],
            }
            email_template.send_mail(
                meeting_obj.id,
                email_values=email_values,
                force_send=True,
            )
            email_template.attachment_ids = [(5, 0, 0)]
        return True
