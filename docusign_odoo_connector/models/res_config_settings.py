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
from odoo import api, fields, models
from odoo.exceptions import UserError
from . import docusign


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    docusign_environment = fields.Selection([
        ('demo', 'Demo / Sandbox'),
        ('production', 'Production'),
    ], string='DocuSign Environment', default='demo',
       help="Select 'Demo / Sandbox' for developer testing or 'Production' for live DocuSign accounts.")
    docusign_integrator_key = fields.Char(
        help="Docusign Integrator key"
    )
    docusign_account_id_data = fields.Char(
        string='Docusign Account Id',
        help="Docusign user account ID"
    )
    docusign_webhook_secret = fields.Char(
        string='DocuSign Connect Secret Key',
        help="Secret key generated in DocuSign Connect (HMAC) to authenticate webhook notifications."
    )
    docusign_user_id_data = fields.Char(
        string='Docusign User Id',
        help="Docusign user ID"
    )
    docusign_private_key_ids = fields.Many2many(
        'ir.attachment',
        'docusign_config_private_key_rel',
        'config_id',
        'attachment_id',
        string='RSA KeyPair',
        help="RSA KeyPair attachment"
    )
    docusign_reminder_days = fields.Integer(
        string="Reminder Days Before Expiry",
        default=2,
        config_parameter='docusign_odoo_connector.reminder_days',
        help="Number of days before document expiry to send automated signing reminder emails."
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        credential = self.env['docusign.credentials'].sudo().search(
            [('company_id', '=', self.env.company.id)], limit=1
        )
        if not credential:
            credential = self.env['docusign.credentials'].sudo().search([], limit=1)
        if credential:
            res.update({
                'docusign_environment': credential.environment or 'demo',
                'docusign_integrator_key': credential.integrator_key or '',
                'docusign_account_id_data': credential.account_id_data or '',
                'docusign_user_id_data': credential.user_id_data or '',
                'docusign_webhook_secret': credential.webhook_secret or '',
                'docusign_private_key_ids': [(6, 0, credential.private_key_ids.ids)],
            })
        return res

    def set_values(self):
        res = super().set_values()
        for record in self:
            credential = self.env['docusign.credentials'].sudo().search(
                [('company_id', '=', self.env.company.id)], limit=1
            )
            if not credential:
                credential = self.env['docusign.credentials'].sudo().search([], limit=1)

            vals = {
                'name': 'DocuSign Credentials',
                'environment': record.docusign_environment or 'demo',
                'integrator_key': record.docusign_integrator_key or '',
                'account_id_data': record.docusign_account_id_data or '',
                'user_id_data': record.docusign_user_id_data or '',
                'webhook_secret': record.docusign_webhook_secret or '',
                'private_key_ids': [(6, 0, record.docusign_private_key_ids.ids)],
                'company_id': self.env.company.id,
            }
            if credential:
                credential.sudo().write(vals)
            elif record.docusign_integrator_key or record.docusign_user_id_data:
                self.env['docusign.credentials'].sudo().create(vals)
        return res

    def action_test_credentials(self):
        """Test DocuSign credentials directly from Settings"""
        self.ensure_one()
        environment = self.docusign_environment or 'demo'
        integrator_key = self.docusign_integrator_key
        account_id_data = self.docusign_account_id_data
        user_id_data = self.docusign_user_id_data
        private_key_ids = self.docusign_private_key_ids

        if not (integrator_key and user_id_data and account_id_data and private_key_ids):
            credential = self.env['docusign.credentials'].sudo().search(
                [('company_id', '=', self.env.company.id)], limit=1
            )
            if not credential:
                credential = self.env['docusign.credentials'].sudo().search([], limit=1)
            if credential:
                environment = environment or credential.environment or 'demo'
                integrator_key = integrator_key or credential.integrator_key
                account_id_data = account_id_data or credential.account_id_data
                user_id_data = user_id_data or credential.user_id_data
                private_key_ids = private_key_ids or credential.private_key_ids

        if not (integrator_key and user_id_data and account_id_data and private_key_ids):
            raise UserError(self.env._("Please fill in all DocuSign credentials before testing."))

        status = docusign.action_login_docusign(
            user_id_data,
            account_id_data,
            integrator_key,
            private_key_ids,
            environment=environment
        )
        if status != 200:
            raise UserError(self.env._("Connection Failed!"))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': self.env._("Connection Successful !"),
                'type': 'success',
                'sticky': False,
            }
        }
