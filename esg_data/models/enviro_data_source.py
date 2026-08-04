# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from __future__ import annotations

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EnviroDataSource(models.Model):
    """
    Base data source record for ESG emission factor providers.

    One record per configured provider.
    Provider subclasses (in separate modules) extend the `provider` selection
    via `selection_add` and implement the abstract interface methods.

    Usage pattern (provider subclass in enviro_data_climatiq):

        class EnviroDataSource(models.Model):
            _inherit = "enviro.data.source"

            provider = fields.Selection(
                selection_add=[("climatiq", "Climatiq")],
                ondelete={"climatiq": "cascade"},
            )

            def _sync_emission_factors(self):
                # implement Climatiq factor sync here
                ...
    """
    _name = "enviro.data.source"
    _description = "Enviro Data Source"
    _inherit = ["mail.thread"]
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Name", required=True, tracking=True)
    provider = fields.Selection(
        selection=[],
        string="Provider",
        required=True,
        tracking=True,
    )
    api_key = fields.Char(string="API Key")
    url = fields.Char(
        string="URL",
        compute="_compute_url",
        store=True,
        readonly=False,
        help="Base URL for the provider API. Leave blank to use the provider default.",
    )

    @api.depends("provider")
    def _compute_url(self):
        """Override in provider subclasses to suggest a default URL per provider.
        Guard with `if not rec.url` so manual edits are never overwritten.
        """
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    notes = fields.Text(string="Notes")

    # ── Abstract interface ────────────────────────────────────────────────────

    def action_test_connection(self):
        """Validate API key and connectivity. Override in provider subclass."""
        self.ensure_one()
        raise UserError(
            _("Provider '%s' does not support connection testing.") % self.provider
        )

    def _sync_emission_factors(self):
        """Pull emission factors from the provider and upsert into enviro.emission.factor."""
        return None
