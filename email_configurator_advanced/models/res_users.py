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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class ResUsers(models.Model):
    """Extend users with the mail provider and app password used to
    generate their outgoing and incoming mail servers."""
    _inherit = 'res.users'

    pwd = fields.Char(
        string='App Password',
        compute='_compute_pwd', inverse='_inverse_pwd', copy=False,
        user_writeable=True,
        help='Enter the app password of the email. It is write-only: it is '
             'saved on the mail servers (readable by administrators only) '
             'and never stored on the user.')
    provider = fields.Many2one(
        comodel_name='provider.server',
        user_writeable=True,
        help='Select a provider from the list.')
    mail_server_id = fields.Many2one(
        comodel_name='ir.mail_server',
        string='Outgoing Mail Server',
        readonly=True,
        ondelete='set null',
        copy=False,
        help='Outgoing mail server generated for this user.')
    fetchmail_server_id = fields.Many2one(
        comodel_name='fetchmail.server',
        string='Incoming Mail Server',
        readonly=True,
        ondelete='set null',
        copy=False,
        help='Incoming mail server generated for this user.')
    automail = fields.Boolean(
        help='Enabled when mail server configuration fields are required on the user form.',
        compute='_compute_automail')

    def _compute_pwd(self):
        """The password is write-only, so it is never read back."""
        for user in self:
            user.pwd = False

    def _inverse_pwd(self):
        """Save a newly entered password on the user's mail servers."""
        for user in self:
            if not user.pwd:
                continue
            if not user.provider:
                raise UserError(self.env._(
                    'Select a provider before entering the app password.'))
            user._sync_mail_servers(password=user.pwd)

    @api.depends_context('uid')
    def _compute_automail(self):
        """Compute the value based on the field in the setting."""
        automail = self.env['ir.config_parameter'].sudo().get_bool(
            'email_configurator_advanced.automail_server')
        for user in self:
            user.automail = automail

    def _check_mail_config_access(self):
        """Only the user themselves or an administrator may configure the
        mail servers of a user."""
        if self != self.env.user and not self.env.user.has_group(
                'base.group_system'):
            raise AccessError(self.env._(
                'You can only configure your own mail servers.'))

    def _get_mail_servers(self):
        """Return the user's (outgoing, incoming) servers, if they exist."""
        self.ensure_one()
        mail_server = self.mail_server_id
        fetchmail_server = self.fetchmail_server_id
        # Fallback to link existing unlinked servers if present
        if not mail_server and self.provider:
            email = self.email or self.partner_id.email
            if email:
                mail_server = self.env['ir.mail_server'].sudo().search([
                    ('smtp_user', '=', email),
                    ('name', '=', self.provider.name),
                ], limit=1)
                if mail_server:
                    self.sudo().mail_server_id = mail_server
        if not fetchmail_server and self.provider:
            email = self.email or self.partner_id.email
            if email:
                fetchmail_server = self.env['fetchmail.server'].sudo().search([
                    ('user', '=', email),
                    ('name', '=', self.provider.name),
                ], limit=1)
                if fetchmail_server:
                    self.sudo().fetchmail_server_id = fetchmail_server
        return mail_server, fetchmail_server

    def _sync_mail_servers(self, password=None):
        """Create or update the mail servers from the provider settings.
        The password is only changed when one is given."""
        self.ensure_one()
        self._check_mail_config_access()
        email = self.email or self.partner_id.email
        if not email:
            raise UserError(self.env._('Set an email address first.'))
        provider = self.provider
        mail_server, fetchmail_server = self._get_mail_servers()
        smtp_vals = {
            'smtp_encryption': provider.smtp_encryption,
            'smtp_debug': provider.smtp_debug,
            'smtp_host': provider.smtp_host,
            'smtp_port': provider.smtp_port,
            'smtp_user': email,
        }
        fetch_vals = {
            'server': provider.server,
            'port': provider.port,
            'server_type': provider.server_type,
            'is_ssl': provider.is_ssl,
            'user': email,
        }
        if password:
            smtp_vals['smtp_pass'] = password
            fetch_vals['password'] = password
        if mail_server:
            mail_server.sudo().write(smtp_vals)
        elif password:
            mail_server = self.env['ir.mail_server'].sudo().create(
                dict(smtp_vals, name=provider.name))
            self.sudo().mail_server_id = mail_server
        if fetchmail_server:
            fetchmail_server.sudo().write(fetch_vals)
        elif password:
            fetchmail_server = self.env['fetchmail.server'].sudo().create(
                dict(fetch_vals, name=provider.name))
            self.sudo().fetchmail_server_id = fetchmail_server
        return mail_server, fetchmail_server

    def action_confirm(self):
        """Update the mail servers and test the incoming and outgoing
        connections."""
        self.ensure_one()
        if not self.provider:
            raise UserError(self.env._('Select a provider'))
        mail_server, fetchmail_server = self._sync_mail_servers()
        if not (mail_server and fetchmail_server):
            raise UserError(self.env._(
                'Enter the app password and save before testing.'))
        mail_server.sudo().test_smtp_connection()
        fetchmail_server.sudo().button_confirm_login()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Connection Successful'),
                'type': 'success',
                'message': self.env._(
                    'Your connection is successfully established'),
                'sticky': False,
            }
        }

    def action_fetch(self):
        """Fetch the mails of the given users."""
        for user in self:
            email = user.email or user.partner_id.email
            if not (user.provider and email):
                continue
            fetchmail_server = user._get_mail_servers()[1]
            if fetchmail_server:
                fetchmail_server.sudo().fetch_mail()

    @api.model
    def _cron_fetch_mail(self):
        """Scheduler action: fetch the mails of every user with a provider."""
        self.sudo().search([('provider', '!=', False)]).action_fetch()
