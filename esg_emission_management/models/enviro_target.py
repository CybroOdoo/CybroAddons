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

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EnviroTarget(models.Model):
    _name = "enviro.target"
    _description = "ESG Reduction Target"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "year desc, company_id"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    year = fields.Integer(
        required=True,
        default=lambda self: fields.Date.context_today(self).year,
        tracking=True,
    )
    reporting_period_id = fields.Many2one(
        "enviro.reporting.period",
        string="Reporting Period",
        domain="[('company_id', '=', company_id)]",
        tracking=True,
        check_company=True,
        index=True,
    )
    baseline_tonnes = fields.Float(required=True, tracking=True)
    target_reduction_pct = fields.Float(string="Reduction Target (%)", required=True, tracking=True)
    target_tonnes = fields.Float(compute="_compute_target_tonnes", store=True)
    actual_tonnes = fields.Float(compute="_compute_actual_tonnes")
    progress_pct = fields.Float(compute="_compute_progress_pct")

    _sql_constraints = [
        (
            "target_company_period_uniq",
            "unique(company_id, reporting_period_id)",
            "Only one target is allowed per company and reporting period.",
        ),
    ]

    @api.depends("company_id", "year", "reporting_period_id")
    def _compute_name(self) -> None:
        for target in self:
            period = target.reporting_period_id.name if target.reporting_period_id else str(target.year)
            target.name = f"{target.company_id.name or ''} {period}"

    @api.depends("baseline_tonnes", "target_reduction_pct")
    def _compute_target_tonnes(self) -> None:
        for target in self:
            target.target_tonnes = target.baseline_tonnes * (1 - target.target_reduction_pct / 100.0)

    @api.depends("baseline_tonnes", "target_tonnes", "actual_tonnes")
    def _compute_progress_pct(self) -> None:
        for target in self:
            expected_reduction = target.baseline_tonnes - target.target_tonnes
            actual_reduction = target.baseline_tonnes - target.actual_tonnes
            target.progress_pct = (actual_reduction / expected_reduction * 100.0) if expected_reduction else 0.0

    def _compute_actual_tonnes(self) -> None:
        for target in self:
            if target.reporting_period_id:
                domain = [
                    ("company_id", "=", target.company_id.id),
                    ("state", "=", "logged"),
                    ("reporting_period_id", "=", target.reporting_period_id.id),
                ]
            else:
                start = fields.Date.to_date(f"{target.year}-01-01")
                end = fields.Date.to_date(f"{target.year}-12-31")
                domain = [
                    ("company_id", "=", target.company_id.id),
                    ("state", "=", "logged"),
                    ("date", ">=", start),
                    ("date", "<=", end),
                ]
            entries = self.env["enviro.emission.record"].search(domain)
            target.actual_tonnes = sum(entries.mapped("co2e_tonnes"))

    @api.constrains("year", "baseline_tonnes", "target_reduction_pct")
    def _check_values(self) -> None:
        for target in self:
            if target.year < 1900:
                raise ValidationError("Enter a valid target year.")
            if target.baseline_tonnes < 0:
                raise ValidationError("Baseline tonnes must be zero or greater.")
            if target.target_reduction_pct < 0 or target.target_reduction_pct > 100:
                raise ValidationError("Reduction target must be between 0 and 100 percent.")
