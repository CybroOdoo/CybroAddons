# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: NIHALA KP(<https://www.cybrosys.com>)
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
from email.utils import formataddr

from odoo import models, fields
import datetime


class ScheduleLog(models.Model):
    """To schedule the log note and message inside the chatter"""
    _name = 'schedule.log'
    _description = "Schedule log note in chatter"

    body = fields.Html(string="Body", help="Content of the log", required="1")
    partner_ids = fields.Many2many('res.partner', string='Recipients',
                                   help='To whom the log is Mentioned')
    time = fields.Datetime(
        default=lambda self: fields.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'),
        string="Scheduled Time",
        help="Time at which the log is scheduled",
        required="1")
    attachment_ids = fields.Many2many(comodel_name='ir.attachment',
                                      string="Attachments", help="Attachments")
    is_log = fields.Boolean(string='Is Log', default=False,
                            help="To check whether log note or scheduled "
                                 "messages")
    model = fields.Char(string='Related Model', help="Related Model")
    model_reference = fields.Integer(string="Related Document Id",
                                     help="Related Document Id")
    status = fields.Selection([('draft', "Schedule"), ('post', "Post")],
                              string='Status', default='draft',
                              help="Status of the Message")

    def action_save(self):
        """Display notification when messages are scheduled"""
        if self.body:
            self.env.registry.clear_cache()
            current_time = fields.Datetime.now().replace(second=0)
            scheduled_time = fields.Datetime.from_string(self.time).replace(
                second=0)
            time_difference = abs(
                (current_time - scheduled_time).total_seconds())
            acceptable_difference = 5
            if time_difference <= acceptable_difference:
                user_id = self.env.user.commercial_partner_id
                partner_ids = self.partner_ids.ids
                if user_id.id in self.partner_ids.ids:
                    partner_ids.remove(user_id.id)
                model = self.env[self.model].sudo().browse(
                    self.model_reference)
                if not self.is_log:
                    message = model.message_post(
                        author_id=self.create_uid.partner_id.id,
                        email_from=self.create_uid.partner_id.email,
                        body=self.body,
                        attachment_ids=self.attachment_ids.ids,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )
                    for mail in message.mail_ids:
                        mail.send()
                    self.status = 'post'
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload_context',
                    }

                else:
                    message = model.message_post(
                        author_id=self.create_uid.partner_id.id,
                        email_from=self.create_uid.partner_id.email,
                        body=self.body,
                        partner_ids=partner_ids,
                        attachment_ids=self.attachment_ids.ids,
                        reply_to=formataddr((self.create_uid.partner_id.name, 'email.from.1@test.example.com'))
                    )

                message.notification_ids = [fields.Command.clear()]
                message.notification_ids = [fields.Command.create({
                    'res_partner_id': pid
                }) for pid in partner_ids]
                self.status = 'post'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload_context',
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Title',
                        'message': "Message scheduled successfully.",
                        'sticky': True,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

    def schedule(self):
        """To schedule the log note"""
        date = datetime.datetime.now()
        date_sec = date.replace(second=0).strftime('%Y-%m-%d %H:%M:%S')
        date_max = date.replace(second=59).strftime('%Y-%m-%d %H:%M:%S')
        scheduled_lognotes = self.env['schedule.log'].search(
            [
                ('status', '=', 'draft'),
                ('time', '>=', date_sec),
                ('time', '<=', date_max),
            ]
        )
        for rec in scheduled_lognotes:
            user_id = rec.env.user.commercial_partner_id
            partner_ids = rec.partner_ids.ids
            if user_id.id in rec.partner_ids.ids:
                partner_ids.remove(user_id.id)
            model = self.env[rec.model].sudo().browse(
                rec.model_reference)
            if not rec.is_log:
                message = model.message_post(
                    author_id=rec.create_uid.partner_id.id,
                    email_from=rec.create_uid.partner_id.email,
                    body=rec.body,
                    attachment_ids=rec.attachment_ids.ids,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
                for mail in message.mail_ids:
                    mail.send()
                rec.status = 'post'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                message = model.message_post(
                    author_id=rec.create_uid.partner_id.id,
                    email_from=rec.create_uid.partner_id.email,
                    body=rec.body,
                    partner_ids=partner_ids,
                    attachment_ids=rec.attachment_ids.ids,
                )
                message.notification_ids = [fields.Command.clear()]
                message.notification_ids = [fields.Command.create({
                    'res_partner_id': pid
                }) for pid in partner_ids]
                rec.status = 'post'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload_context',
                }
