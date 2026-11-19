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


class ProviderServer(models.Model):
    """Class to model provider server in settings->technical"""
    _name = 'provider.server'
    _description = 'Provider Server'

    name = fields.Char(
        help='Enter the provider name.')
    smtp_encryption = fields.Selection(
        selection=[('none', 'None'),
                   ('starttls', 'TLS (STARTTLS)'),
                   ('ssl', 'SSL/TLS')],
        string='Connection Encryption',
        required=True, default='none',
        help='Choose the connection encryption scheme')
    smtp_debug = fields.Boolean(
        string='Debugging',
        help="If enabled, the full output of SMTP sessions will "
             "be written to the server log at DEBUG level "
             "(this is very verbose and may include confidential info!)")
    smtp_host = fields.Char(
        string='SMTP Server',
        help="Hostname or IP of SMTP server",
        required=True)
    smtp_port = fields.Integer(
        default=25,
        help="SMTP Port. Usually 465 for SSL, and 25 or 587 for other cases.")
    server = fields.Char(
        string='Server Name',
        help="Hostname or IP of the mail server",
        required=True)
    port = fields.Integer(help='Specify the port number.')
    server_type = fields.Selection(
        selection=[
            ('imap', 'IMAP Server'),
            ('pop', 'POP Server'),
            ('local', 'Local Server'), ],
        index=True, required=True,
        default='pop')
    is_ssl = fields.Boolean(
        string='SSL/TLS',
        help="Connections are encrypted with SSL/TLS through a dedicated port "
             "(default: IMAPS=993, POP3S=995)")
    active = fields.Boolean(
        default=True,
        help='Enable for the model to active state.')

    @api.onchange('smtp_encryption')
    def _onchange_smtp_encryption(self):
        """Function to change the smtp port number of outgoing mail server
        based on encryption."""
        if self.smtp_encryption == 'ssl':
            self.smtp_port = 465
        else:
            self.smtp_port = 25

    @api.onchange('server_type', 'is_ssl')
    def _onchange_server_type(self):
        """Function to change the port number of incoming mail server based
        on server type."""
        self.port = 0
        if self.server_type == 'pop':
            self.port = self.is_ssl and 995 or 110
        elif self.server_type == 'imap':
            self.port = self.is_ssl and 993 or 143
