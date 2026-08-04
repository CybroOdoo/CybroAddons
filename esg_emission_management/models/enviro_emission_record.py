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
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class EnviroEmissionRecord(models.Model):
    _name = "enviro.emission.record"
    _description = "Enviro Emission Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    factor_id = fields.Many2one(
        "enviro.emission.factor",
        string="Emission Factor",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        tracking=True,
        check_company=True,
    )
    enviro_activity_type_id = fields.Many2one("enviro.activity.type", string="Activity Type", tracking=True)
    category = fields.Selection(related="factor_id.category", store=True, readonly=True)
    scope = fields.Selection(related="factor_id.scope", store=True, readonly=True)
    calculation_type = fields.Selection(related="factor_id.calculation_type", readonly=True)
    quantity = fields.Float(default=1.0, required=True, tracking=True)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", tracking=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(currency_field="currency_id", tracking=True)
    co2e_kg = fields.Float(string="kgCO2e", compute="_compute_emissions", store=True)
    co2e_tonnes = fields.Float(string="tCO2e", compute="_compute_emissions", store=True)
    uncertainty_kg = fields.Float(string="Uncertainty kgCO2e", compute="_compute_emissions", store=True)
    source_type = fields.Selection(
        selection=[
            ("manual", "Manual"),
            ("invoice", "Invoice"),
            ("journal", "Journal"),
            ("fleet", "Fleet Log"),
            ("stock", "Stock / Logistics"),
            ("import", "Import"),
        ],
        default="manual",
        required=True,
        tracking=True,
    )
    account_move_id = fields.Many2one("account.move", string="Related Journal Entry", check_company=True)
    account_move_line_id = fields.Many2one("account.move.line", string="Related Journal Item", check_company=True, copy=False)
    partner_id = fields.Many2one("res.partner", related="account_move_id.partner_id", store=True)
    reporting_period_id = fields.Many2one(
        "enviro.reporting.period",
        string="Reporting Period",
        domain="[('company_id', '=', company_id), ('state', '!=', 'locked')]",
        tracking=True,
        check_company=True,
        index=True,
    )
    site_id = fields.Many2one(
        "enviro.site",
        string="Site / Facility",
        domain="[('company_id', '=', company_id)]",
        tracking=True,
        check_company=True,
        index=True,
    )
    notes = fields.Text()
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("logged", "Logged"),
            ("missing", "Missing Factor"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )

    @api.onchange("factor_id")
    def _onchange_factor_id(self) -> None:
        for entry in self:
            if not entry.factor_id:
                continue
            if entry.factor_id.calculation_type == "quantity":
                entry.uom_id = entry.factor_id.uom_id
            else:
                entry.currency_id = entry.factor_id.currency_id

    @api.depends(
        "factor_id",
        "factor_id.kg_co2e_per_unit",
        "factor_id.uncertainty_pct",
        "factor_id.calculation_type",
        "factor_id.uom_id",
        "factor_id.currency_id",
        "quantity",
        "uom_id",
        "amount",
        "currency_id",
    )
    def _compute_emissions(self) -> None:
        for entry in self:
            multiplier = 0.0
            if entry.factor_id:
                if entry.factor_id.calculation_type == "amount":
                    if entry.currency_id and entry.factor_id.currency_id:
                        multiplier = entry.currency_id._convert(
                            entry.amount,
                            entry.factor_id.currency_id,
                            entry.company_id,
                            entry.date or fields.Date.context_today(entry),
                            round=False,
                        )
                elif entry.uom_id and entry.factor_id.uom_id:
                    multiplier = entry.uom_id._compute_quantity(
                        entry.quantity,
                        entry.factor_id.uom_id,
                        round=False,
                    )
            entry.co2e_kg = multiplier * entry.factor_id.kg_co2e_per_unit if entry.factor_id else 0.0
            entry.co2e_tonnes = entry.co2e_kg / 1000.0
            entry.uncertainty_kg = entry.co2e_kg * (entry.factor_id.uncertainty_pct / 100.0) if entry.factor_id else 0.0

    @api.constrains("quantity", "amount")
    def _check_positive_values(self) -> None:
        for entry in self:
            if entry.quantity < 0:
                raise ValidationError(_("Quantity cannot be negative. Use an offset factor for reductions."))
            if entry.amount < 0:
                raise ValidationError(_("Amount cannot be negative. Use an offset factor for reductions."))

    @api.constrains("reporting_period_id", "state")
    def _check_period_not_locked(self) -> None:
        for entry in self:
            if (
                entry.reporting_period_id
                and entry.reporting_period_id.state == "locked"
                and entry.state == "logged"
            ):
                raise ValidationError(
                    _(
                        "Reporting period '%(period)s' is locked. "
                        "Unlock it before adding or modifying logged entries.",
                        period=entry.reporting_period_id.name,
                    )
                )

    def action_log(self) -> None:
        for entry in self:
            entry.state = "logged" if entry.factor_id else "missing"

    def action_reset_to_draft(self) -> None:
        self.write({"state": "draft"})

    def action_cancel(self) -> None:
        self.write({"state": "cancelled"})

    def unlink(self) -> bool:
        if any(entry.state == "logged" for entry in self):
            raise UserError(_("Logged emission records cannot be deleted. Cancel them instead."))
        return super().unlink()

    @api.model
    def get_dashboard_data(self, date_from=None, date_to=None, scopes=None) -> dict:
        today = fields.Date.context_today(self)
        date_from = fields.Date.to_date(date_from) if date_from else today.replace(month=1, day=1)
        date_to = fields.Date.to_date(date_to) if date_to else today
        domain = [
            ("state", "=", "logged"),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("company_id", "in", self.env.companies.ids),
        ]
        if scopes and set(scopes) != {"scope1", "scope2", "scope3"}:
            domain += [("scope", "in", list(scopes))]
        total = sum(self.search(domain).mapped("co2e_tonnes"))
        by_scope = {
            scope: value
            for scope, value in self._read_group(
                domain + [("scope", "!=", False)],
                ["scope"],
                ["co2e_tonnes:sum"],
            )
        }
        by_month = {
            month: value
            for month, value in self._read_group(
                domain,
                ["date:month"],
                ["co2e_tonnes:sum"],
            )
        }
        
        # ── Category grouping for pie chart ───────────────────────────────────
        by_category = {
            category: value
            for category, value in self._read_group(
                domain + [("category", "!=", False)],
                ["category"],
                ["co2e_tonnes:sum"],
            )
        }

        # ── Site grouping ─────────────────────────────────────────────────────
        by_site = {
            site: value
            for site, value in self._read_group(
                domain + [("site_id", "!=", False)],
                ["site_id"],
                ["co2e_tonnes:sum"],
            )
        }

        # ── Activity Type grouping ────────────────────────────────────────────
        by_activity = {
            activity: value
            for activity, value in self._read_group(
                domain + [("enviro_activity_type_id", "!=", False)],
                ["enviro_activity_type_id"],
                ["co2e_tonnes:sum"],
            )
        }

        # ── Previous period logic (YoY / MoM) ─────────────────────────────────
        duration = (date_to - date_from).days
        prev_date_to = date_from - timedelta(days=1)
        prev_date_from = prev_date_to - timedelta(days=duration)
        prev_domain = [
            ("state", "=", "logged"),
            ("date", ">=", prev_date_from),
            ("date", "<=", prev_date_to),
            ("company_id", "in", self.env.companies.ids),
        ]
        if scopes and set(scopes) != {"scope1", "scope2", "scope3"}:
            prev_domain += [("scope", "in", list(scopes))]
            
        prev_total = sum(self.search(prev_domain).mapped("co2e_tonnes"))
        prev_by_scope = {
            scope: value
            for scope, value in self._read_group(
                prev_domain + [("scope", "!=", False)],
                ["scope"],
                ["co2e_tonnes:sum"],
            )
        }
        prev_scope1 = prev_by_scope.get("scope1", 0.0)
        prev_scope2 = prev_by_scope.get("scope2", 0.0)
        prev_scope3 = prev_by_scope.get("scope3", 0.0)

        scope1 = by_scope.get("scope1", 0.0)
        scope2 = by_scope.get("scope2", 0.0)
        scope3 = by_scope.get("scope3", 0.0)
        # ── Missing-factor alert: respect period + scope ──────────────────────
        missing_domain = [
            ("state", "=", "missing"),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("company_id", "in", self.env.companies.ids),
        ]
        if scopes and set(scopes) != {"scope1", "scope2", "scope3"}:
            missing_domain += [("scope", "in", list(scopes))]
        missing_count = self.search_count(missing_domain)
        # ── Retired offsets: filter by purchase_date within period ────────────
        retired_offsets = sum(self.env["enviro.offset"].search([
            ("company_id", "in", self.env.companies.ids),
            ("purchase_date", ">=", date_from),
            ("purchase_date", "<=", date_to),
            ("state", "in", ("partially_retired", "retired")),
        ]).mapped("retired_tonnes"))
        # ── Recent entries: respect period + scope ────────────────────────────
        recent_entries = self.search(
            domain,
            order="date desc, id desc",
            limit=5,
        )
        # ── Targets: cover all years spanned by the selected period ─────────
        target_years = list(range(date_from.year, date_to.year + 1))
        current_targets = self.env["enviro.target"].search([
            ("company_id", "in", self.env.companies.ids),
            ("year", "in", target_years),
        ])
        target_baseline = sum(current_targets.mapped("baseline_tonnes"))
        target_tonnes = sum(current_targets.mapped("target_tonnes"))
        expected_reduction = target_baseline - target_tonnes
        actual_reduction = target_baseline - total
        target_progress = (actual_reduction / expected_reduction * 100.0) if expected_reduction else 0.0
        # ── Initiatives: filter by overlap with the selected period ─────────
        initiatives = self.env["enviro.initiative"].search([
            ("company_id", "in", self.env.companies.ids),
            ("state", "!=", "cancelled"),
            ("start_date", "<=", date_to),
            "|",
            ("end_date", "=", False),
            ("end_date", ">=", date_from),
        ])
        active_initiatives = initiatives.filtered(lambda i: i.state in ("planned", "in_progress"))
        recent_initiatives = active_initiatives.sorted(
            key=lambda i: (i.start_date or fields.Date.to_date("1900-01-01"), i.id),
            reverse=True,
        )[:5]
        return {
            "year": date_from.year,
            "date_from": fields.Date.to_string(date_from),
            "date_to": fields.Date.to_string(date_to),
            "total": round(total, 3),
            "prev_total": round(prev_total, 3),
            "total_diff_pct": round(((total - prev_total) / prev_total * 100.0) if prev_total else 0.0, 1),
            "scope1": round(scope1, 3),
            "prev_scope1": round(prev_scope1, 3),
            "scope1_diff_pct": round(((scope1 - prev_scope1) / prev_scope1 * 100.0) if prev_scope1 else 0.0, 1),
            "scope2": round(scope2, 3),
            "prev_scope2": round(prev_scope2, 3),
            "scope2_diff_pct": round(((scope2 - prev_scope2) / prev_scope2 * 100.0) if prev_scope2 else 0.0, 1),
            "scope3": round(scope3, 3),
            "prev_scope3": round(prev_scope3, 3),
            "scope3_diff_pct": round(((scope3 - prev_scope3) / prev_scope3 * 100.0) if prev_scope3 else 0.0, 1),
            "scope1_pct": round(scope1 / total * 100.0, 1) if total else 0.0,
            "scope2_pct": round(scope2 / total * 100.0, 1) if total else 0.0,
            "scope3_pct": round(scope3 / total * 100.0, 1) if total else 0.0,
            "categories": [
                {"label": cat.capitalize(), "value": round(val, 3)}
                for cat, val in sorted(by_category.items(), key=lambda x: x[1], reverse=True)
            ],
            "sites": [
                {"label": site.name, "value": round(val, 3)}
                for site, val in sorted(by_site.items(), key=lambda x: x[1], reverse=True)
            ],
            "activities": [
                {"label": act.name, "value": round(val, 3)}
                for act, val in sorted(by_activity.items(), key=lambda x: x[1], reverse=True)
            ],
            "retired_offsets": round(retired_offsets, 3),
            "net_total": round(total - retired_offsets, 3),
            "missing_count": missing_count,
            "target_progress": round(max(min(target_progress, 100.0), 0.0), 1),
            "target_reduction_pct": round(sum(current_targets.mapped("target_reduction_pct")) / len(current_targets), 1) if current_targets else 0.0,
            "target_baseline": round(target_baseline, 3),
            "active_initiatives_count": len(active_initiatives),
            "initiative_expected_saving": round(sum(initiatives.mapped("expected_saving_tonnes")), 3),
            "initiative_actual_saving": round(sum(initiatives.mapped("actual_saving_tonnes")), 3),
            "months": [
                {"label": month.strftime("%b %Y"), "value": round(value, 3)}
                for month, value in sorted(by_month.items())
            ],
            "recent_entries": [
                {
                    "id": entry.id,
                    "name": entry.name,
                    "date": fields.Date.to_string(entry.date),
                    "state": entry.state,
                    "scope": entry.scope,
                    "co2e_tonnes": round(entry.co2e_tonnes, 3),
                }
                for entry in recent_entries
            ],
            "recent_initiatives": [
                {
                    "name": initiative.name,
                    "state": initiative.state,
                    "progress": round(initiative.progress, 1),
                    "expected_saving_tonnes": round(initiative.expected_saving_tonnes, 3),
                    "actual_saving_tonnes": round(initiative.actual_saving_tonnes, 3),
                }
                for initiative in recent_initiatives
            ],
        }
