# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import datetime
import pytz
from odoo import api, fields, models
from odoo.exceptions import UserError


class MailComposeMessage(models.TransientModel):
    """This class add a field called schedule_time in this model, to have the
    date and time for scheduling """
    _inherit = 'mail.compose.message'

    schedule_time = fields.Datetime(string='Schedule Time',
                                    help='Schedule date and time')

    @api.onchange('schedule_time')
    def _onchange_schedule_time(self):
        """When the field 'schedule_time' change, it will replace the seconds
        as zero"""
        if self.schedule_time:
            self.schedule_time = self.schedule_time.replace(second=0)

    def action_schedule_mail(self):
        """This function is used to create a record in schedule.mail and
        display the scheduled mail as a message in chatter """
        email_from = self.author_id.email
        attachment_list = []
        for attachment in self.attachment_ids:
            attachment_list.append(attachment.id)
        partner_list = []
        for partner in self.partner_ids:
            partner_list.append(partner.id)
        schedule_mail = self.env['mail.mail'].create({
            'email_from': email_from,
            'subject': self.subject,
            'body_html': self.body,
            'scheduled_date': self.schedule_time,
            'recipient_ids': partner_list,
            'attachment_ids': attachment_list,
        })
        utc_current_datetime = fields.Datetime.now()
        user_tz = pytz.timezone(self.env.context.get(
            'tz') or self.env.user.tz)  # Access the time zone
        date_today = pytz.utc.localize(utc_current_datetime).astimezone(
            user_tz)  # Access local time
        user_current_datetime = date_today.strftime(
            '%Y-%m-%d %H:%M:%S')  # Converted to string and removed the utc time difference
        user_current_date = datetime.datetime.strptime(user_current_datetime,
                                                       "%Y-%m-%d %H:%M:%S").replace(
            second=0)
        if not self.schedule_time:
            raise UserError('Invalid Schedule time')
        if self.schedule_time and self.schedule_time > user_current_date:
            raise UserError('Invalid Schedule time')
        model = self.env.context['default_res_model']
        model_id = self.env['ir.model'].search([('model', '=', model)], limit=1)
        record_id = self.env.context['default_res_ids']
        record = self.env[model].browse(record_id)
        activity = {
            'activity_type_id': self.env.ref(
                'schedule_mail_to_send.mail_activity_schedule').id,
            'summary': self.subject,
            'note': self.body,
            'date_deadline': self.schedule_time,
            'res_model_id': model_id.id,
            'res_id': record.id,
            'schedule_mail_id': schedule_mail.id
        }
        record.activity_schedule(**activity)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def send_scheduled_mail(self):
        """This function is called by a scheduled action in each minute to
        send the scheduled mails"""
        utc_current_datetime = fields.Datetime.now()
        # Access the time zone
        user_tz = pytz.timezone(self.env.context.get(
            'tz') or self.env.user.tz)
        # Access local time
        date_today = pytz.utc.localize(utc_current_datetime).astimezone(
            user_tz)
        # Converted to string and removed the utc time difference
        user_current_datetime = date_today.strftime(
            '%Y-%m-%d %H:%M:%S')
        # Again converted to datetime type and replace the seconds with 0
        user_current_date = datetime.datetime.strptime(
            user_current_datetime,
            "%Y-%m-%d %H:%M:%S").replace(
            second=0)
        scheduled_mail_rec = self.env['mail.mail'].search(
            [('scheduled_date', '<=', user_current_date)])
        if scheduled_mail_rec:
            for record in scheduled_mail_rec:
                record.send()
                planned_activity = self.env['mail.activity'].search(
                    [('schedule_mail_id', '=', record.id)])
                # unlink the planned activity
                planned_activity.sudo().action_feedback(self)
