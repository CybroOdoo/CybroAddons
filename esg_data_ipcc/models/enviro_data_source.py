# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
##############################################################################
from __future__ import annotations

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_EFDB_BASE = "https://www.ipcc-nggip.iges.or.jp/EFDB"

REGION_COUNTRY_CODES = {
    "Africa": ["AO", "BF", "BI", "BJ", "BW", "CD", "CF", "CG", "CI", "CM", "CV", "DJ", "DZ", "EG", "EH", "ER", "ET", "GA", "GH", "GM", "GN", "GQ", "GW", "KE", "KM", "LR", "LS", "LY", "MA", "MG", "ML", "MR", "MU", "MW", "MZ", "NA", "NE", "NG", "RW", "SC", "SD", "SL", "SN", "SO", "SS", "ST", "SZ", "TD", "TG", "TN", "TZ", "UG", "ZA", "ZM", "ZW"],
    "Asia": ["AF", "AM", "AZ", "BD", "BH", "BN", "BT", "CN", "HK", "ID", "IL", "IN", "IQ", "IR", "JO", "JP", "KG", "KH", "KP", "KR", "KW", "KZ", "LA", "LB", "LK", "MO", "MM", "MN", "MV", "MY", "NP", "OM", "PH", "PK", "PS", "QA", "SA", "SG", "SY", "TH", "TJ", "TM", "TR", "TW", "UZ", "VN", "YE"],
    "Europe": ["AD", "AL", "AT", "BA", "BE", "BG", "BY", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GB", "GE", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MC", "MD", "ME", "MK", "MT", "NL", "NO", "PL", "PT", "RO", "RS", "RU", "SE", "SI", "SK", "SM", "UA", "VA"],
    "Latin America and Caribbean": ["AG", "AR", "BS", "BB", "BZ", "BO", "BR", "CL", "CO", "CR", "CU", "DM", "DO", "EC", "SV", "GD", "GT", "GY", "HT", "HN", "JM", "MX", "NI", "PA", "PY", "PE", "KN", "LC", "VC", "SR", "TT", "UY", "VE"],
    "North America": ["CA", "US", "BM", "GL", "PM"],
    "Oceania": ["AS", "AU", "CK", "FJ", "FM", "GU", "KI", "MH", "NR", "NC", "NZ", "NU", "MP", "PW", "PG", "WS", "SB", "TK", "TO", "TV", "VU", "AQ", "TF"]
}


class EnviroDataSource(models.Model):
    """Adds IPCC EFDB as a data source provider."""
    _inherit = "enviro.data.source"

    provider = fields.Selection(
        selection_add=[("ipcc", "IPCC EFDB")],
        ondelete={"ipcc": "cascade"},
    )

    ipcc_region = fields.Selection(
        selection=[
            ("Africa", "Africa"),
            ("Asia", "Asia"),
            ("Europe", "Europe"),
            ("Latin America and Caribbean", "Latin America and Caribbean"),
            ("North America", "North America"),
            ("Oceania", "Oceania"),
        ],
        string="IPCC Region",
    )
    ipcc_country_ids = fields.Many2many(
        "res.country",
        string="IPCC Countries",
    )

    @api.depends("provider")
    def _compute_url(self):
        super()._compute_url()
        for rec in self:
            if not rec.url and rec.provider == "ipcc":
                rec.url = _EFDB_BASE

    @api.onchange("ipcc_region")
    def _onchange_ipcc_region(self):
        for rec in self:
            if rec.ipcc_region:
                allowed_codes = REGION_COUNTRY_CODES.get(rec.ipcc_region, [])
                if rec.ipcc_country_ids:
                    rec.ipcc_country_ids = rec.ipcc_country_ids.filtered(lambda c: c.code in allowed_codes)
                return {"domain": {"ipcc_country_ids": [("code", "in", allowed_codes)]}}
            return {"domain": {"ipcc_country_ids": []}}

    ipcc_last_import = fields.Datetime(string="Last Import", readonly=True, copy=False)
    ipcc_imported_count = fields.Integer(
        string="Imported Factors",
        compute="_compute_ipcc_imported_count",
    )

    @api.depends()
    def _compute_ipcc_imported_count(self):
        for rec in self:
            rec.ipcc_imported_count = self.env["enviro.emission.factor"].search_count([
                ("source_id", "=", rec.id),
            ]) if rec.provider == "ipcc" else 0

    def action_test_connection(self):
        self.ensure_one()
        if self.provider != "ipcc":
            return super().action_test_connection()
        raise UserError(_("IPCC EFDB is a public database — no connection test required."))

    def action_ipcc_import(self):
        self.ensure_one()
        result = self.env["enviro.emission.factor"].action_import_from_ipcc(source_id=self.id)
        self.ipcc_last_import = fields.Datetime.now()
        return result

    def action_ipcc_update(self):
        self.ensure_one()
        result = self.env["enviro.emission.factor"].action_update_from_ipcc(source_id=self.id)
        self.ipcc_last_import = fields.Datetime.now()
        return result
