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
#############################################################################
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tools import formataddr


class MailingList(models.Model):
    """Add the mail on subscription and the drip mass mailing to the mailing
    lists."""
    _inherit = 'mailing.list'

    mail_contact = fields.Boolean(
        string="Enable Mail on Subscription",
        help="Send the selected template to the contacts who subscribe to "
             "this mailing list")
    template_id = fields.Many2one(
        'drip.template', string="Select Template",
        help="Template sent to the contacts who subscribe to this mailing "
             "list")
    mass_mailing_enable = fields.Boolean(
        string="Enable Mass Mailing",
        help="Send the drip templates to the contacts of this mailing list, "
             "the given number of days after the start date")
    start_date = fields.Date(
        help="Date the days of the drip templates are counted from")
    end_date = fields.Date(
        help="No drip template is sent after this date")
    server_id = fields.Many2one(
        'ir.mail_server', string="Outgoing Mail Server",
        help="Outgoing mail server used to send the drip mails")
    template_ids = fields.One2many(
        'mailing.list.templates', 'mailing_id', string="Drip Templates",
        help="Drip templates to send, and when")
    drip_history_ids = fields.One2many(
        'drip.mailing.history', 'mailing_id')
    drip_count = fields.Integer(
        compute="_compute_drip_count",
        help="Number of drip mails sent")

    @api.model_create_multi
    def create(self, vals_list):
        """Send the subscription mail of the lists, also when they are
        joined through the many2many field, which does not create the
        subscriptions through their model."""
        records = super(
            MailingList, self.with_context(drip_subscription_mail_pending=True),
        ).create(vals_list)
        # The many2many shares the subscription table: read it again
        records.invalidate_recordset(['subscription_ids'])
        records.subscription_ids._send_drip_subscription_mail()
        return records.with_env(self.env)

    def write(self, vals):
        """Send the subscription mail of the lists joined by this write."""
        if not {'contact_ids', 'subscription_ids'} & vals.keys():
            return super().write(vals)
        subscriptions = self.subscription_ids
        res = super(
            MailingList, self.with_context(drip_subscription_mail_pending=True),
        ).write(vals)
        self.invalidate_recordset(['subscription_ids'])
        (self.subscription_ids - subscriptions)._send_drip_subscription_mail()
        return res

    @api.depends('drip_history_ids')
    def _compute_drip_count(self):
        """Count the drip mails sent to the contacts of the list."""
        for mailing_list in self:
            mailing_list.drip_count = len(mailing_list.drip_history_ids)

    @api.constrains('start_date', 'end_date')
    def _check_drip_dates(self):
        """The drip mass mailing cannot end before it starts."""
        for mailing_list in self:
            if (mailing_list.start_date and mailing_list.end_date
                    and mailing_list.end_date < mailing_list.start_date):
                raise ValidationError(self.env._(
                    "The end date of the drip mass mailing of %(list)s cannot "
                    "be before its start date.", list=mailing_list.name))

    def _get_drip_email_from(self):
        """Return a sender address accepted by the outgoing mail server of
        the list, like the mass mailings do."""
        self.ensure_one()
        user_email = self.create_uid.email_formatted
        notification_email = self.env[
            'ir.mail_server']._get_default_from_address()
        server = self.server_id
        if server and not server._match_from_filter(
                user_email, server.from_filter) and server._match_from_filter(
                notification_email, server.from_filter):
            return notification_email
        return (user_email or notification_email
                or self.env.company.email_formatted)

    def _send_drip_mail(self, template, contacts):
        """Queue one mail of the drip template per contact, through the
        outgoing mail server of the list, so that the recipients do not see
        each other."""
        self.ensure_one()
        contacts = contacts.filtered('email')
        if not template or not contacts:
            return self.env['mail.mail']
        email_from = self._get_drip_email_from()
        mails = self.env['mail.mail'].sudo().create([{
            'subject': template.name,
            'body_html': template.mail_body,
            'email_from': email_from,
            'email_to': formataddr((contact.name or '', contact.email)),
            'mail_server_id': self.server_id.id,
            'attachment_ids': [Command.set(template.attachment_ids.ids)],
        } for contact in contacts])
        self.env.ref('mail.ir_cron_mail_scheduler_action')._trigger()
        return mails

    def _get_drip_recipients(self):
        """Return the contacts of the list who did not opt out of it and are
        not blacklisted."""
        self.ensure_one()
        return self.subscription_ids.filtered(
            lambda subscription: not subscription.opt_out,
        ).contact_id.filtered(lambda contact: not contact.is_blacklisted)

    @api.model
    def _action_drip_mass_mailing(self):
        """Send the drip templates due today, from the scheduled action."""
        today = fields.Date.context_today(self)
        mailing_lists = self.search([
            ('mass_mailing_enable', '=', True),
            ('start_date', '<=', today),
            ('end_date', '>=', today),
        ])
        for mailing_list in mailing_lists:
            for line in mailing_list.template_ids:
                if (mailing_list.start_date + timedelta(days=line.days_after)
                        != today):
                    continue
                if self.env['drip.mailing.history'].search_count([
                    ('mailing_id', '=', mailing_list.id),
                    ('template_id', '=', line.template_id.id),
                    ('send_date', '=', today),
                ], limit=1):
                    continue
                contacts = mailing_list._get_drip_recipients().filtered(
                    'email')
                mailing_list._send_drip_mail(line.template_id, contacts)
                self.env['drip.mailing.history'].create([{
                    'name': line.name or line.template_id.name,
                    'contact_id': contact.id,
                    'mailing_id': mailing_list.id,
                    'template_id': line.template_id.id,
                    'send_date': today,
                } for contact in contacts])

    def get_drip_history(self):
        """Open the drip mails sent to the contacts of the list."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Drip History"),
            'view_mode': 'list,form',
            'res_model': 'drip.mailing.history',
            'domain': [('mailing_id', '=', self.id)],
            'context': {'create': False},
        }
