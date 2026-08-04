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

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EnviroSite(models.Model):
    _name = "enviro.site"
    _description = "Enviro Site / Facility"
    _inherit = ["mail.thread"]
    _order = "complete_name"
    _check_company_auto = True
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"

    name = fields.Char(required=True, tracking=True)
    complete_name = fields.Char(compute="_compute_complete_name", store=True, recursive=True)
    parent_id = fields.Many2one(
        "enviro.site",
        string="Parent Site",
        index=True,
        ondelete="restrict",
        check_company=True,
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many("enviro.site", "parent_id", string="Sub-Sites")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    site_type = fields.Selection(
        selection=[
            ("hq", "Headquarters"),
            ("office", "Office"),
            ("warehouse", "Warehouse"),
            ("factory", "Factory / Manufacturing"),
            ("data_centre", "Data Centre"),
            ("retail", "Retail"),
            ("other", "Other"),
        ],
        default="office",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    street = fields.Char()
    city = fields.Char()
    country_id = fields.Many2one("res.country")
    latitude = fields.Float(digits=(10, 7))
    longitude = fields.Float(digits=(10, 7))
    floor_area_m2 = fields.Float(
        string="Floor Area (m²)",
        help="Used for energy intensity calculations (kWh/m²).",
    )
    notes = fields.Text()
    entry_count = fields.Integer(compute="_compute_entry_count")

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self) -> None:
        for site in self:
            if site.parent_id:
                site.complete_name = f"{site.parent_id.complete_name} / {site.name}"
            else:
                site.complete_name = site.name

    @api.constrains("parent_id")
    def _check_parent_id(self) -> None:
        if not self._check_recursion():
            raise ValidationError(_("A site cannot be its own parent (circular reference)."))

    def _compute_entry_count(self) -> None:
        grouped = self.env["enviro.emission.record"]._read_group(
            [("site_id", "in", self.ids)],
            ["site_id"],
            ["__count"],
        )
        counts = {site.id: count for site, count in grouped}
        for site in self:
            site.entry_count = counts.get(site.id, 0)

    def action_view_entries(self) -> dict:
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Emission Records — %s", self.name),
            "res_model": "enviro.emission.record",
            "view_mode": "list,form,pivot,graph",
            "domain": [("site_id", "=", self.id)],
            "context": {"default_site_id": self.id},
        }
