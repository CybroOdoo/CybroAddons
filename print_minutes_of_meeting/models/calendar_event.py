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
from odoo import api, fields, models


class CalendarEvent(models.Model):
    """Inheriting fields for in calendar event to get the details """
    _inherit = 'calendar.event'

    responsible_user_id = fields.Many2one(
        'res.users',
        help="The person who is responsible for the event",
    )
    note_taker_id = fields.Many2one(
        'res.partner',
        domain="[('id', 'in', partner_ids)]",
        help="The note taker",
    )
    absent_member_ids = fields.Many2many(
        'res.partner',
        'res_partner_absent_member_rel',
        domain="[('id', 'in', partner_ids)]",
        help="Absent members of the meeting",
    )
    agenda_ids = fields.One2many(
        'meeting.agenda', 'calendar_event_id',
        help='The meeting agendas',
    )
    actions_ids = fields.One2many(
        'meeting.actions', 'calendar_event_id',
        string='Actions/Decisions',
        help='The meeting actions or decisions',
    )
    notes = fields.Html(string='Conclusions', help='Meeting conclusions')
    is_user = fields.Boolean(
        compute='_compute_is_user',
        help='Is user or not',
    )

    @api.depends('responsible_user_id')
    def _compute_is_user(self):
        """Compute whether responsible user is the current logged-in user."""
        for rec in self:
            rec.is_user = bool(rec.responsible_user_id.id == self.env.user.id)

    def action_send_mail(self):
        """Send meeting minutes email with PDF attachment to attendees."""
        # Clean up previous attachment created by this module for this event
        self.env['ir.attachment'].search([
            ('res_model', '=', 'calendar.event'),
            ('res_id', 'in', self.ids),
            ('name', '=', 'Minutes of Meeting.pdf'),
        ]).unlink()

        report_ref = (
            'print_minutes_of_meeting.action_minutes_of_meeting_report'
        )
        report_template_id = self.env['ir.actions.report']._render_qweb_pdf(
            report_ref=report_ref,
            data=None,
            res_ids=self.ids,
        )
        ir_values = {
            'name': "Minutes of Meeting.pdf",
            'type': 'binary',
            'raw': report_template_id[0],
            'mimetype': 'application/pdf',
            'res_model': 'calendar.event',
            'res_id': self.id,
        }
        data_id = self.env['ir.attachment'].create(ir_values)

        template_id = self.env.ref(
            'print_minutes_of_meeting.email_template_minutes_of_meeting')
        context = {
            'name': self.name,
        }
        email_values = {
            'recipient_ids': [(4, partner) for partner in
                              self.partner_ids.ids],
            'email_from': self.responsible_user_id.email,
            'attachment_ids': [(4, data_id.id)],
        }
        template_id.with_context(context=context).send_mail(
            self.id, email_values=email_values, force_send=True
        )


class MeetingAgenda(models.Model):
    """Class for adding meeting agenda"""
    _name = 'meeting.agenda'
    _description = 'Meeting Agenda'
    _rec_name = 'topic'

    topic = fields.Char(help='Agenda Topic')
    description = fields.Char(help='Description of the Meeting')
    is_discussed = fields.Boolean(
        string='Discussed',
        help='The topic is discussed or not',
    )
    calendar_event_id = fields.Many2one(
        'calendar.event', string='Event',
        help='The Calendar Event',
    )


class MeetingActions(models.Model):
    """Class for adding meeting actions"""
    _name = 'meeting.actions'
    _description = 'Meeting Actions'

    def _responsible_partner_id_domain(self):
        """Return the domain for responsible partner"""
        return [('id', 'in', self.calendar_event_id.partner_ids.ids)]

    action = fields.Char(help='The action taken during the meeting')
    description = fields.Char(help='The action description')
    agenda_item_id = fields.Many2one(
        'meeting.agenda', string='Agenda',
        help='The agenda item',
    )
    responsible_partner_id = fields.Many2one(
        'res.partner',
        help='The responsible partner for the action',
        domain=lambda self: self._responsible_partner_id_domain(),
    )
    assigned_partner_ids = fields.Many2many(
        'res.partner',
        help='The assigned partners of the action',
    )
    calendar_event_id = fields.Many2one(
        'calendar.event', string='Event',
        help='Related event of the action',
    )
    deadline = fields.Date(help='Deadline for the action')
