# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class AuthOAuthProvider(models.Model):
    """Inherits auth.oauth.provider to add fields"""
    _inherit = "auth.oauth.provider"

    client_secret = fields.Char(string="Client Secret",help="Client Secret Key")
    is_github = fields.Boolean(compute='_compute_is_github')

    def _compute_is_github(self):
        """
            Compute the value for is_github field based on the auth_endpoint
            value.

            This method iterates over the records to compute the value for the
            `is_github` field.
            It checks if each record's authentication endpoint contains 'github'.
            If the authentication endpoint contains 'github', it sets the
            `is_github` field to True.
            Otherwise, it sets the `is_github` field to False.

        """
        for rec in self:
            rec.is_github = rec.auth_endpoint and 'github' in rec.auth_endpoint
