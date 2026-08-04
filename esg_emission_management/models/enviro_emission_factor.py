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


class EnviroEmissionFactor(models.Model):
    _name = "enviro.emission.factor"
    _description = "Enviro Emission Factor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scope, category, name"
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        help="Leave empty to share this factor with every company.",
    )
    category = fields.Selection(
        selection=[
            ("energy", "Energy"),
            ("fleet", "Fleet"),
            ("travel", "Travel"),
            ("waste", "Waste"),
            ("water", "Water"),
            ("procurement", "Procurement"),
            ("supplier", "Supplier"),
            ("offset", "Offset"),
            ("other", "Other"),
        ],
        default="energy",
        required=True,
        tracking=True,
    )
    scope = fields.Selection(
        selection=[
            ("scope1", "Direct (Scope 1)"),
            ("scope2", "Indirect Energy (Scope 2)"),
            ("scope3", "Other Indirect (Scope 3)"),
        ],
        string="Reporting Class",
        default="scope1",
        required=True,
        tracking=True,
    )
    calculation_type = fields.Selection(
        selection=[
            ("quantity", "Quantity"),
            ("amount", "Amount"),
        ],
        default="quantity",
        required=True,
        tracking=True,
    )
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )
    kg_co2e_per_unit = fields.Float(
        string="kgCO2e per Unit",
        required=True,
        digits=(16, 6),
        tracking=True,
    )
    use_gas_breakdown = fields.Boolean(
        string="Use Gas Breakdown",
        help="Compute kgCO2e per unit from gas lines instead of a single total factor.",
        tracking=True,
    )
    gas_line_ids = fields.One2many(
        "enviro.emission.factor.gas.line",
        "factor_id",
        string="Gas Emissions",
    )
    gas_breakdown_kg_co2e_per_unit = fields.Float(
        string="Gas Breakdown kgCO2e per Unit",
        compute="_compute_gas_breakdown_kg_co2e_per_unit",
        store=True,
        digits=(16, 6),
    )
    uncertainty_pct = fields.Float(string="Uncertainty (%)", digits=(16, 4), tracking=True)
    source = fields.Char(default="Custom", tracking=True)
    code = fields.Char(
        string="Reference Code",
        index=True,
        copy=False,
        help="External reference code for this factor (e.g. ADEME ID, IPCC EF ID).",
    )
    region = fields.Char(
        string="Region",
        help="Geographic region this factor applies to.",
    )
    valid_from = fields.Date(string="Valid From", help="Start of the period this factor is valid for.")
    valid_to = fields.Date(string="Valid To", help="End of the period this factor is valid for.")
    notes = fields.Text()
    entry_count = fields.Integer(compute="_compute_entry_count")

    _sql_constraints = [
        (
            "positive_factor_value",
            "CHECK(kg_co2e_per_unit >= 0)",
            "The emission factor value must be zero or greater.",
        ),
        (
            "positive_uncertainty",
            "CHECK(uncertainty_pct >= 0)",
            "The uncertainty percentage must be zero or greater.",
        ),
    ]

    @api.constrains("calculation_type", "uom_id", "currency_id")
    def _check_factor_unit(self) -> None:
        for factor in self:
            if factor.calculation_type == "quantity" and not factor.uom_id:
                raise ValidationError(_("Quantity-based factors require a unit of measure."))
            if factor.calculation_type == "amount" and not factor.currency_id:
                raise ValidationError(_("Amount-based factors require a currency."))

    @api.depends("gas_line_ids.kg_co2e_per_unit")
    def _compute_gas_breakdown_kg_co2e_per_unit(self) -> None:
        for factor in self:
            factor.gas_breakdown_kg_co2e_per_unit = sum(factor.gas_line_ids.mapped("kg_co2e_per_unit"))

    @api.onchange("use_gas_breakdown", "gas_line_ids")
    def _onchange_gas_breakdown(self) -> None:
        for factor in self:
            if factor.use_gas_breakdown:
                factor.kg_co2e_per_unit = sum(factor.gas_line_ids.mapped("kg_co2e_per_unit"))

    def _sync_gas_breakdown_total(self) -> None:
        for factor in self.filtered("use_gas_breakdown"):
            factor.kg_co2e_per_unit = sum(factor.gas_line_ids.mapped("kg_co2e_per_unit"))

    def write(self, vals):
        result = super().write(vals)
        if "use_gas_breakdown" in vals:
            self._sync_gas_breakdown_total()
        return result

    @api.depends("name", "scope", "category")
    def _compute_display_name(self) -> None:
        scope_labels = dict(self._fields["scope"].selection)
        category_labels = dict(self._fields["category"].selection)
        for factor in self:
            factor.display_name = _(
                "%(name)s (%(scope)s / %(category)s)",
                name=factor.name,
                scope=scope_labels.get(factor.scope),
                category=category_labels.get(factor.category),
            )

    def _compute_entry_count(self) -> None:
        grouped = self.env["enviro.emission.record"]._read_group(
            [("factor_id", "in", self.ids)],
            ["factor_id"],
            ["__count"],
        )
        counts = {factor.id: count for factor, count in grouped}
        for factor in self:
            factor.entry_count = counts.get(factor.id, 0)

    def action_view_entries(self) -> dict:
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Emission Records"),
            "res_model": "enviro.emission.record",
            "view_mode": "list,form,kanban,pivot,graph",
            "domain": [("factor_id", "=", self.id)],
            "context": {"default_factor_id": self.id},
        }
