# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models


class AuthOAuthProvider(models.Model):
    """Inherit auth.oauth.provider to add GitHub-specific configuration fields."""

    _inherit = "auth.oauth.provider"

    # Fields declarations
    client_secret = fields.Char(
        string="Client Secret",
        help="Client secret key provided by the GitHub OAuth application.")
    is_github = fields.Boolean(
        string="Is GitHub",
        compute='_compute_is_github',
        help="Indicates whether this OAuth provider is configured for GitHub.")

    # Compute methods
    def _compute_is_github(self):
        """Compute whether the OAuth provider is GitHub based on its authentication endpoint."""
        for rec in self:
            rec.is_github = bool(
                rec.auth_endpoint and 'github' in rec.auth_endpoint)
