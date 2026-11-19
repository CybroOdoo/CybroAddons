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
from odoo.exceptions import AccessError


class AuthenticationWizard(models.TransientModel):
    """ Wizard to enter Dropbox authorization code. """
    _name = 'dropbox.authentication'
    _description = 'Dropbox Authentication'

    dropbox_authorization_code = fields.Char(string='Authorization Code',
                                             help='Dropbox Authorization Code')
    dropbox_auth_url = fields.Char(string='Dropbox Authentication URL',
                                    compute='_compute_dropbox_auth_url',
                                    help='Dropbox Authentication URL')

    @api.depends('dropbox_authorization_code')
    def _compute_dropbox_auth_url(self):
        """ Compute method to update the Dropbox Authentication URL based on the
        provided authorization code. """
        dbx_config = self.env['res.config.settings'].browse(
            self.env.context.get('active_id'))
        for rec in self:
            rec.dropbox_auth_url = dbx_config.get_dropbox_auth_url()

    def action_setup_dropbox_token(self):
        """ Action method to set up the Dropbox refresh token using the provided
        authorization code. """
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._("Access Denied: Only administrators can configure Dropbox integration."))
        dbx_config = self.env['res.config.settings'].browse(
            self.env.context.get('active_id'))
        dbx_config.set_dropbox_refresh_token(
            self.dropbox_authorization_code)
