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
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AuthOAuthProvider(models.Model):
    """Inherits auth.oauth.provider to add fields"""
    _inherit = "auth.oauth.provider"

    client_secret = fields.Char(string="Client Secret", help="Client Secret Key")
    is_github = fields.Boolean(
        string="Is GitHub Provider",
        compute='_compute_is_github',
        store=True,
    )

    @api.depends('auth_endpoint', 'validation_endpoint')
    def _compute_is_github(self):
        """
        Compute the value for is_github field based on auth_endpoint
        or validation_endpoint containing 'github'.
        """
        for rec in self:
            rec.is_github = bool(
                (rec.auth_endpoint and 'github' in rec.auth_endpoint.lower()) or
                (rec.validation_endpoint and 'github' in rec.validation_endpoint.lower())
            )
