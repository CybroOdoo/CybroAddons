# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Noorjahan @ Cybrosys, (odoo@cybrosys.com)
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
import base64
from odoo import models, fields, api


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    responsible_user_id = fields.Many2one('res.users',
                                          help="The person who is responsible for the event")
    note_taker_id = fields.Many2one('res.partner',
                                    domain="[('id', 'in', partner_ids)]",
                                    help="The note taker")
    absent_member_ids = fields.Many2many('res.partner',
                                         'res_partner_absent_member_rel',
                                         domain="[('id', 'in', partner_ids)]",
                                         help="Absent members of the meeting")
    agenda_ids = fields.One2many('meeting.agenda', 'calendar_event_id',
                                 string='Agenda')
    actions_ids = fields.One2many('meeting.actions', 'calendar_event_id',
                                  string='Actions/Decisions')
    notes = fields.Html(string='Conclusions')
    is_user = fields.Boolean(compute='compute_is_user')

    @api.depends('responsible_user_id')
    def compute_is_user(self):
        """Function to set is the responsible user is same as the login user"""
        for rec in self:
            rec.is_user = bool(rec.responsible_user_id.id == self.env.user.id)

    def send_mail(self):
        """Send mail"""
        report_template_id = self.env['ir.actions.report']._render_qweb_pdf(
            report_ref='print_minutes_of_meeting.action_minutes_of_meeting_report',
            data=None,
            res_ids=self.ids,
        )
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Minutes of Meeting",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)

        template_id = self.env.ref(
            'print_minutes_of_meeting.email_template_minutes_of_meeting')
        template_id.attachment_ids = [(6, 0, [data_id.id])]
        context = {
            'name': self.name,
        }
        email_values = {
            'recipient_ids': [(4, partner) for partner in self.partner_ids.ids],
            'email_from': self.responsible_user_id.email
        }
        self.env['mail.template'].browse(template_id.id).with_context(
            context=context).send_mail(self.id, email_values=email_values,
                                       force_send=True)
        template_id.attachment_ids = [(3, data_id.id)]


class MeetingAgenda(models.Model):
    _name = 'meeting.agenda'
    _rec_name = 'topic'

    topic = fields.Char()
    description = fields.Char()
    is_discussed = fields.Boolean('Discussed')
    calendar_event_id = fields.Many2one('calendar.event')


class MeetingActions(models.Model):
    _name = 'meeting.actions'

    def _responsible_partner_id_domain(self):
        """return the domain for responsible partner"""
        return [('id', 'in', self.calendar_event_id.partner_ids.ids)]

    action = fields.Char()
    description = fields.Char()
    agenda_item_id = fields.Many2one('meeting.agenda')
    responsible_partner_id = fields.Many2one('res.partner',
                                             domain=_responsible_partner_id_domain)
    assigned_partner_ids = fields.Many2many('res.partner')
    calendar_event_id = fields.Many2one('calendar.event')
    deadline = fields.Date()
