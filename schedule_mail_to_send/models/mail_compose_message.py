# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
            'scheduled_user_tz': pytz.timezone(self.env.context.get('tz') or self.env.user.tz),
        })
        # Get the user's timezone (fallback to UTC if not set)
        user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        # Get current UTC time and convert to user's timezone
        utc_current_datetime = fields.Datetime.now()  # Naive UTC datetime
        local_current_datetime = fields.Datetime.context_timestamp(
            self.with_context(tz=user_tz), timestamp=utc_current_datetime
        )
        # Handle schedule_time (assumed to be UTC in the database)
        schedule_time = self.schedule_time
        if isinstance(schedule_time, str):
            # If schedule_time is a string, parse it to datetime (assuming UTC)
            schedule_time = fields.Datetime.from_string(schedule_time)
        # Convert schedule_time to user's timezone
        if schedule_time:
            schedule_time = fields.Datetime.context_timestamp(
                self.with_context(tz=user_tz), timestamp=schedule_time
            )
        else:
            raise UserError('Invalid Schedule time')
        # Truncate seconds for comparison (to match your original logic)
        local_current_datetime = local_current_datetime.replace(second=0,
                                                                microsecond=0)
        schedule_time = schedule_time.replace(second=0, microsecond=0)
        # Validate schedule time
        if schedule_time < local_current_datetime:
            raise UserError('Scheduled time cannot be in the past')
        model = self.env.context['default_res_model']
        model_id = self.env['ir.model'].search([('model', '=', model)],
                                               limit=1)
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

    def action_send_scheduled_mail(self):
        """Executed by cron every minute. Sends emails whose scheduled datetime
        has passed according to the timezone of the user who scheduled them.
        """
        Mail = self.env['mail.mail']
        # Fetch all mails having schedule date set
        scheduled_mails = Mail.search([('scheduled_date', '!=', False)])
        for mail in scheduled_mails:
            # If no timezone stored, fallback to UTC
            user_tz = mail.scheduled_user_tz or 'UTC'
            # Convert current UTC time → user's timezone
            user_local_now = fields.Datetime.context_timestamp(
                mail.with_context(tz=user_tz),
                fields.Datetime.now()
            ).replace(second=0, microsecond=0)
            # Convert scheduled UTC → user's timezone
            scheduled_dt = fields.Datetime.context_timestamp(
                mail.with_context(tz=user_tz),
                mail.scheduled_date
            ).replace(second=0, microsecond=0)
            # If scheduled time has passed, send mail
            if scheduled_dt <= user_local_now:
                mail.send()
                # Remove any linked scheduled activity
                activity = self.env['mail.activity'].search(
                    [('schedule_mail_id', '=', mail.id)]
                )
                if activity:
                    activity.sudo().action_feedback()
