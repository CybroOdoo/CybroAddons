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
"""Inherited res.users model for API key generation and management."""
import uuid
from odoo import fields, models


class ResUsers(models.Model):
    """This class inherits res.users to add API key generation."""
    _inherit = 'res.users'

    api_key = fields.Char(string="API Key", readonly=True,
                          groups="base.group_system", copy=False,
                          help="API key for connecting with the "
                               "database. The key will be "
                               "generated when authenticating via "
                               "REST API.")

    def generate_api(self, username):
        """Generate an API key for the specified user."""
        users = self.env['res.users'].sudo().search([('login', '=', username)])
        if not users.api_key:
            users.api_key = str(uuid.uuid4())
            key = users.api_key
        else:
            key = users.api_key
        return key
