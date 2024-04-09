# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ashok PK (odoo@cybrosys.com)
#
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
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProviderServer(models.Model):
    """Class to inherit users model to add few fields and functions."""
    _inherit = 'res.users'

    pwd = fields.Char(
        string='Password',
        help='Enter the app password of the email.')
    provider = fields.Many2one(
        comodel_name='provider.server',
        string='Provider',
        help='Select a provider from the list.')
    automail = fields.Boolean(
        string='Automail',
        help='Enable if the auto generate mail server in setting is true.',
        compute='compute_automail',
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
            'email_configurator_advanced.automail_server'))

    @api.depends('automail')
    def compute_automail(self):
        """Function to compute the value based on the field in the setting"""
        if self.env['ir.config_parameter'].sudo().get_param(
                'email_configurator_advanced.automail_server'):
            self.automail = True
        else:
            self.automail = False

    def action_confirm(self):
        """Function to create auto mail server for incoming and outgoing."""
        if self.provider:
            existing_mail_server = self.env['ir.mail_server'].search([
                ('smtp_user', '=', self.email),
                ('name', '=', self.provider.name)], limit=1)
            existing_fetchmail_server = self.env['fetchmail.server'].search([
                ('user', '=', self.email),
                ('name', '=', self.provider.name)], limit=1)
            if existing_mail_server:
                existing_mail_server.write({
                    'smtp_encryption': self.provider.smtp_encryption,
                    'smtp_debug': self.provider.smtp_debug,
                    'smtp_host': self.provider.smtp_host,
                    'smtp_port': self.provider.smtp_port,
                    'smtp_pass': self.pwd,
                })
            else:
                self.env['ir.mail_server'].create({
                    'name': self.provider.name,
                    'smtp_encryption': self.provider.smtp_encryption,
                    'smtp_debug': self.provider.smtp_debug,
                    'smtp_host': self.provider.smtp_host,
                    'smtp_port': self.provider.smtp_port,
                    'smtp_user': self.email,
                    'smtp_pass': self.pwd,
                })
            if existing_fetchmail_server:
                existing_fetchmail_server.write({
                    'server': self.provider.server,
                    'port': self.provider.port,
                    'server_type': self.provider.server_type,
                    'is_ssl': self.provider.is_ssl,
                    'password': self.pwd,
                })
            else:
                self.env['fetchmail.server'].create({
                    'name': self.provider.name,
                    'server': self.provider.server,
                    'port': self.provider.port,
                    'server_type': self.provider.server_type,
                    'is_ssl': self.provider.is_ssl,
                    'user': self.email,
                    'password': self.pwd,
                })
            existing_mail_server.test_smtp_connection()
            existing_fetchmail_server.button_confirm_login()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Successful',
                    'type': 'success',
                    'message': 'Your connection is successfully established',
                    'sticky': False,
                }
            }
        else:
            raise UserError('Select a provider')

    def action_fetch(self):
        """Function for fetching mail on the interval of 1 minute for the
        scheduler action."""
        existing_fetchmail_server = self.env['fetchmail.server'].search([
            ('user', '=', self.email),
            ('name', '=', self.provider.name)], limit=1)
        existing_fetchmail_server.fetch_mail()
