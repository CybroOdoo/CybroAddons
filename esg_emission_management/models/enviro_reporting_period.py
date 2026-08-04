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


class EnviroReportingPeriod(models.Model):
    _name = "enviro.reporting.period"
    _description = "Enviro Reporting Period"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, name"
    _check_company_auto = True

    name = fields.Char(
        required=True,
        tracking=True,
        help="e.g. 'FY 2025', 'H1 2025', 'Q3 2025'",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    date_start = fields.Date(required=True, tracking=True)
    date_end = fields.Date(required=True, tracking=True)
    period_type = fields.Selection(
        selection=[
            ("annual", "Annual"),
            ("semi_annual", "Semi-Annual"),
            ("quarterly", "Quarterly"),
            ("custom", "Custom"),
        ],
        default="annual",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("open", "Open"),
            ("closed", "Closed"),
            ("locked", "Locked"),
        ],
        default="open",
        required=True,
        tracking=True,
    )
    notes = fields.Text()
    entry_count = fields.Integer(compute="_compute_entry_count")
    target_count = fields.Integer(compute="_compute_target_count")

    _sql_constraints = [
        (
            "period_company_name_uniq",
            "unique(company_id, name)",
            "A reporting period with this name already exists for this company.",
        ),
    ]

    @api.constrains("date_start", "date_end", "company_id")
    def _check_dates(self) -> None:
        for period in self:
            if period.date_end <= period.date_start:
                raise ValidationError(_("The end date must be after the start date."))
            overlap = self.search([
                ("id", "!=", period.id),
                ("company_id", "=", period.company_id.id),
                ("date_start", "<=", period.date_end),
                ("date_end", ">=", period.date_start),
            ], limit=1)
            if overlap:
                raise ValidationError(_(
                    "Reporting period '%(new)s' overlaps with existing period '%(existing)s' "
                    "(%(start)s – %(end)s).",
                    new=period.name,
                    existing=overlap.name,
                    start=overlap.date_start,
                    end=overlap.date_end,
                ))

    def _compute_entry_count(self) -> None:
        grouped = self.env["enviro.emission.record"]._read_group(
            [("reporting_period_id", "in", self.ids)],
            ["reporting_period_id"],
            ["__count"],
        )
        counts = {period.id: count for period, count in grouped}
        for period in self:
            period.entry_count = counts.get(period.id, 0)

    def _compute_target_count(self) -> None:
        grouped = self.env["enviro.target"]._read_group(
            [("reporting_period_id", "in", self.ids)],
            ["reporting_period_id"],
            ["__count"],
        )
        counts = {period.id: count for period, count in grouped}
        for period in self:
            period.target_count = counts.get(period.id, 0)

    def action_close(self) -> None:
        self.filtered(lambda p: p.state == "open").write({"state": "closed"})

    def action_lock(self) -> None:
        self.filtered(lambda p: p.state == "closed").write({"state": "locked"})

    def action_reopen(self) -> None:
        self.filtered(lambda p: p.state in ("closed", "locked")).write({"state": "open"})

    def action_view_entries(self) -> dict:
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Emission Records — %s", self.name),
            "res_model": "enviro.emission.record",
            "view_mode": "list,form,pivot,graph",
            "domain": [("reporting_period_id", "=", self.id)],
            "context": {"default_reporting_period_id": self.id},
        }
