# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# -*- coding: utf-8 -*-
import base64
import logging
import pytz
from datetime import timedelta
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import is_html_empty, html2plaintext

_logger = logging.getLogger(__name__)
try:
    import vobject
except ImportError:
    _logger.warning(
        "`vobject` Python module not found, iCal file generation disabled. "
        "Consider installing this module if you want to generate iCal files")
    vobject = None


class Meeting(models.Model):
    """This class is to inherit calendar event model redefine mail button
    function and adding an extra button action."""
    _inherit = 'calendar.event'

    def action_send_ics(self):
        """This function is for sending mail invitations to attendees with
        attached ics file of that event."""
        print(self._get_ics_file().get(self.id))
        attachment_values = {'name': 'Event.ics',
                             'type': 'binary',
                             'datas': base64.b64encode(
                                 self._get_ics_file().get(self.id)),
                             'mimetype': 'text/calendar',
                             'res_model': 'calendar.event',
                             'res_id': self.id}
        attachment = self.env['ir.attachment'].sudo().create(attachment_values)
        email_template = self.env.ref('odoo_icalendar.event_ics_email_template')
        email_values = {'email_to': ', '.join(
            attendee.email for attendee in self.partner_ids),
            'attachment_ids': [(4, attachment.id)]}
        email_template.send_mail(
            self.id, email_values=email_values, force_send=True)
        email_template.attachment_ids = [(5, 0, 0)]

    def action_send_attendee_ics_file(self):
        """Button action to send an ics file attached to mail of the
        attendees."""
        result = {}

        def ics_datetime(idate, allday=False):
            """Format a date and time as an iCalendar-compatible string.
               :param idate: The input date and time.
               :type idate: datetime.datetime
               :param allday: Flag indicating if the event is an all-day event
               (default is False).
               :type allday: bool
               :return: The formatted date and time as a string in the iCalendar
                format.
               :rtype: str or False if idate is None."""
            if idate:
                if allday:
                    return idate
                return idate.replace(tzinfo=pytz.timezone('UTC'))
            return False

        if not vobject:
            return result
        attendee_events = {}
        meeting_obj = []
        for meeting in self:
            meeting_obj = meeting
            for attendee in meeting.partner_ids:
                if attendee.id not in attendee_events:
                    attendee_events[attendee.id] = vobject.iCalendar()
                cal = attendee_events[attendee.id]
                event = cal.add('vevent')
                if not meeting.start or not meeting.stop:
                    raise UserError(
                        _("First you have to specify the date of the "
                          "invitation."))
                event.add('created').value = ics_datetime(fields.Datetime.now())
                event.add('dtstart').value = ics_datetime(meeting.start,
                                                          meeting.allday)
                event.add('dtend').value = ics_datetime(meeting.stop,
                                                        meeting.allday)
                event.add('summary').value = meeting.name
                if not is_html_empty(meeting.description):
                    if 'appointment_type_id' in meeting._fields and \
                            self.appointment_type_id:
                        event.add(
                            'description').value = self. \
                            convert_online_event_desc_to_text(
                            meeting.description)
                    else:
                        event.add('description').value = html2plaintext(
                            meeting.description)
                if meeting.location:
                    event.add('location').value = meeting.location
                if meeting.rrule:
                    event.add('rrule').value = meeting.rrule
                if meeting.alarm_ids:
                    for alarm in meeting.alarm_ids:
                        valarm = event.add('valarm')
                        interval = alarm.interval
                        duration = alarm.duration
                        trigger = valarm.add('TRIGGER')
                        trigger.params['related'] = ["START"]
                        delta = ''
                        if interval == 'days':
                            delta = timedelta(days=duration)
                        elif interval == 'hours':
                            delta = timedelta(hours=duration)
                        elif interval == 'minutes':
                            delta = timedelta(minutes=duration)
                        trigger.value = delta
                        valarm.add('DESCRIPTION').value = alarm.name or 'Odoo'
                attendee_add = event.add('attendee')
                attendee_add.value = 'MAILTO:' + (attendee.email or '')
        for attendee_id, cal in attendee_events.items():
            attendee = self.env['res.partner'].browse(attendee_id)
            attachment_values = {'name': 'All_Events.ics',
                                 'type': 'binary',
                                 'datas': base64.b64encode(
                                     cal.serialize().encode('utf-8')),
                                 'mimetype': 'text/calendar',
                                 'res_model': 'calendar.event',
                                 'res_id': attendee.id}
            attachment = self.env['ir.attachment'].sudo().create(
                attachment_values)
            email_template = self.env.ref(
                'odoo_icalendar.odoo_icalendar_email_template')
            email_values = {'email_to': attendee.email,
                            'email_cc': False,
                            'scheduled_date': False,
                            'recipient_ids': [],
                            'partner_ids': [],
                            'auto_delete': True,
                            'attachment_ids': [(4, attachment.id)]}
            email_template.send_mail(meeting_obj[0].id,
                                     email_values=email_values,
                                     force_send=True)
            email_template.attachment_ids = [(5, 0, 0)]
