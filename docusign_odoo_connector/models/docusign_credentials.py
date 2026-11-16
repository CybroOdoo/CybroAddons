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
from . import docusign
from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError


class DocusignCredentials(models.Model):
    """ To set up the Docusign account credentials for integrating with odoo"""
    _name = 'docusign.credentials'
    _description = "Docusign Credentials Setup"

    name = fields.Char(required=True, help="Name of record")
    environment = fields.Selection([
        ('demo', 'Demo / Sandbox'),
        ('production', 'Production'),
    ], default='demo', required=True,
       help="Select 'Demo / Sandbox' for developer testing or 'Production' for live DocuSign accounts.")
    integrator_key = fields.Char(string="Docusign Integrator Key",
                                 required=True, help="Docusign Integrator key")
    account_id_data = fields.Char(string='Docusign Account Id', required=True,
                                  help="Docusign user account ID")
    user_id_data = fields.Char(string='Docusign User Id', required=True,
                               help="Docusign user ID")
    webhook_secret = fields.Char(
        string='DocuSign Connect Secret Key',
        help="Secret key generated in DocuSign Connect (HMAC) to authenticate webhook notifications. Leave empty if HMAC is not enabled in DocuSign."
    )
    private_key_ids = fields.Many2many('ir.attachment',
                                       string='RSA KeyPair',
                                       required=True,
                                       help="RSA KeyPair attachment")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 help="Company associated with this credential.")

    @api.constrains('private_key_ids')
    def _check_private_key_ids(self):
        for record in self:
            if len(record.private_key_ids) > 1:
                raise ValidationError(
                    self.env._("You can upload only one RSA KeyPair attachment.")
                )

    def action_test_credentials(self):
        """ Function to test whether the credentials are valid or not"""
        status = docusign.action_login_docusign(self.user_id_data,
                                                self.account_id_data,
                                                self.integrator_key,
                                                self.private_key_ids,
                                                environment=self.environment)
        if status != 200:
            raise UserError(self.env._("Connection Failed!"))
        message = self.env._("Connection Successful !")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

