# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Irfan T @ Cybrosys, (odoo@cybrosys.com)
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
from odoo import api, fields, models


class CalendarEvent(models.Model):
    """Inherit calendar to add some extra fields"""
    _inherit = 'calendar.event'

    responsible_user_id = fields.Many2one('res.users',
                                          help="The person who is responsible "
                                               "for the event",
                                          string="Responsible User")
    note_taker_id = fields.Many2one('res.partner',
                                    domain="[('id', 'in', partner_ids)]",
                                    help="The note taker",
                                    string="Note Taker")
    absent_member_ids = fields.Many2many('res.partner',
                                         'res_partner_absent_member_rel',
                                         domain="[('id', 'in', partner_ids)]",
                                         help="Absent members of the meeting",
                                         string="Absent Member")
    agenda_ids = fields.One2many('meeting.agenda', 'calendar_event_id',
                                 string='Agenda', help="Agenda of meeting")
    actions_ids = fields.One2many('meeting.action', 'calendar_event_id',
                                  string='Actions/Decisions',
                                  help="Required action for agenda of meeting")
    notes = fields.Html(string='Conclusions',
                        help="Conclusion of meeting")
    is_user = fields.Boolean(compute='_compute_is_user',
                             string="Is User", help="Is this user")

    @api.depends('responsible_user_id')
    def _compute_is_user(self):
        """Function to set is the responsible user is same as the login user"""
        for rec in self:
            rec.is_user = bool(rec.responsible_user_id.id == self.env.user.id)

    def action_send_mail(self):
        """Send mail"""
        report_template_id, _ = self.env.ref(
            'print_minutes_of_meeting.action_minutes_of_meeting_report') \
            .with_context(
            force_report_rendering=True)._render_qweb_pdf(
            data=None, res_ids=self.ids, )
        data_id = self.env['ir.attachment'].create({
            'name': "Minutes of Meeting",
            'type': 'binary',
            'datas': base64.b64encode(report_template_id),
            'store_fname': base64.b64encode(report_template_id),
            'mimetype': 'application/pdf',
        })
        template_id = self.env.ref(
            'print_minutes_of_meeting.email_template_minutes_of_meeting')
        template_id.attachment_ids = [(6, 0, [data_id.id])]
        email_values = {
            'email_to': ','.join(self.partner_ids.mapped('email')),
            'email_from': self.responsible_user_id.email
        }
        self.env['mail.template'].browse(template_id.id).with_context(
            context=self.name).send_mail(self.id, email_values=email_values,
                                         force_send=True)
        template_id.attachment_ids = [(3, data_id.id)]
