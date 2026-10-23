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
#############################################################################
"""Mail compose message wizard extension for scheduling emails."""

import ast
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MailComposeMessage(models.TransientModel):
    """This class adds a field called schedule_time in this model to allow
    scheduling the date and time for sending emails."""
    _inherit = 'mail.compose.message'

    schedule_time = fields.Datetime(
        help='Schedule date and time'
    )

    @api.onchange('schedule_time')
    def _onchange_schedule_time(self):
        """When the field 'schedule_time' changes, clear seconds."""
        if self.schedule_time:
            self.schedule_time = self.schedule_time.replace(second=0)

    def action_schedule_mail(self):
        """Schedule the email to be sent at the specified schedule_time,
        create the corresponding mail.mail linked to the record, and log
        a planned activity on the record."""
        self.ensure_one()
        schedule_time = (
            fields.Datetime.to_datetime(self.schedule_time)
            if self.schedule_time else False
        )
        if not schedule_time:
            raise UserError(self.env._('Invalid Schedule time.'))

        now_dt = fields.Datetime.now().replace(second=0, microsecond=0)
        sched_dt = schedule_time.replace(second=0, microsecond=0)
        if sched_dt < now_dt:
            raise UserError(
                self.env._('Scheduled time cannot be in the past.')
            )

        model = (
            self.model
            or self.env.context.get('default_model')
            or self.env.context.get('active_model')
            or self.env.context.get('default_res_model')
        )
        if not model:
            raise UserError(
                self.env._('No model specified for scheduled mail.')
            )
        model_id = self.env['ir.model'].search(
            [('model', '=', model)], limit=1
        )
        if not model_id:
            raise UserError(
                self.env._('Invalid model specified for scheduled mail.')
            )

        raw_res_ids = (
            self.res_ids
            or self._evaluate_res_ids()
            or self.env.context.get('default_res_ids')
            or self.env.context.get('active_ids')
            or self.env.context.get('active_id')
            or self.env.context.get('default_res_id')
            or []
        )
        if isinstance(raw_res_ids, str):
            try:
                raw_res_ids = ast.literal_eval(raw_res_ids)
            except (ValueError, SyntaxError):
                raw_res_ids = []
        if isinstance(raw_res_ids, int):
            raw_res_ids = [raw_res_ids]

        res_ids = [
            int(r)
            for r in (
                raw_res_ids
                if isinstance(raw_res_ids, (list, tuple))
                else [raw_res_ids]
            )
            if r and str(r).isdigit()
        ]
        if not res_ids:
            raise UserError(
                self.env._('No record specified for scheduled mail.')
            )
        record = self.env[model].browse(res_ids[0])
        if not record.exists():
            raise UserError(
                self.env._('No record specified for scheduled mail.')
            )

        user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        email_from = self.author_id.email or self.env.user.email_formatted
        schedule_mail = self.env['mail.mail'].create({
            'model': model,
            'res_id': record.id,
            'email_from': email_from,
            'subject': self.subject or '',
            'body_html': self.body or '',
            'scheduled_date': schedule_time,
            'recipient_ids': [
                fields.Command.link(p.id) for p in self.partner_ids
            ],
            'attachment_ids': [
                fields.Command.link(a.id) for a in self.attachment_ids
            ],
            'scheduled_user_tz': user_tz,
        })

        activity_vals = {
            'activity_type_id': self.env.ref(
                'schedule_mail_to_send.mail_activity_schedule'
            ).id,
            'summary': self.subject or self.env._('Scheduled Mail'),
            'note': self.body or '',
            'date_deadline': schedule_time.date(),
            'res_model_id': model_id.id,
            'res_id': record.id,
            'schedule_mail_id': schedule_mail.id,
        }
        record.activity_schedule(**activity_vals)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_send_scheduled_mail(self):
        """Executed by cron to send scheduled emails whose delivery time
        has arrived. Only processes emails created by this module."""
        activity_type = self.env.ref(
            'schedule_mail_to_send.mail_activity_schedule',
            raise_if_not_found=False,
        )
        if not activity_type:
            return
        activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', activity_type.id),
            ('schedule_mail_id', '!=', False),
        ])
        mail_ids = activities.mapped('schedule_mail_id')
        if not mail_ids:
            return

        now_utc = fields.Datetime.now()
        scheduled_mails = self.env['mail.mail'].browse(mail_ids).filtered(
            lambda m: m.exists()
            and m.state in ('outgoing', 'exception')
            and m.scheduled_date
            and m.scheduled_date <= now_utc
        )
        for mail in scheduled_mails:
            try:
                mail.send()
            except Exception as exc:
                _logger.warning(
                    'Failed to send scheduled mail %s: %s', mail.id, exc
                )
                continue
            mail_id = mail.id
            activity = activities.filtered(
                lambda a, mid=mail_id: a.schedule_mail_id == mid
            )
            if activity:
                activity.sudo().action_feedback(
                    feedback=self.env._('Scheduled mail has been sent.')
                )
