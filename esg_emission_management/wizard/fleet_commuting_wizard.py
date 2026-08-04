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
from odoo.exceptions import UserError


class FleetCommutingWizard(models.TransientModel):
    """
    Calculates Scope 1 commuting emissions for a given period.

    Formula per assignment log:
        overlap_days  = days the assignment overlaps with the selected period
        round_trip_km = employee.km_home_work × 2
        office_ratio  = company.enviro_weekly_office_days / 7
        co2_gkm       = vehicle.co2  (gCO₂/km — manufacturer spec)

        total_km      = overlap_days × round_trip_km × office_ratio
        co2e_kg       = total_km × co2_gkm / 1000
    """
    _name = "enviro.fleet.commuting.wizard"
    _description = "Enviro Fleet Commuting Emissions Wizard"

    date_start = fields.Date(string="Period Start", required=True)
    date_end = fields.Date(string="Period End", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    preview_line_ids = fields.One2many(
        "enviro.fleet.commuting.wizard.line",
        "wizard_id",
        string="Preview",
        readonly=True,
    )

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for wizard in self:
            if wizard.date_start > wizard.date_end:
                raise UserError(_("Period Start must be before Period End."))

    def action_preview(self):
        self.ensure_one()
        self.preview_line_ids.unlink()
        lines = self._compute_lines()
        self.env["enviro.fleet.commuting.wizard.line"].create([
            {
                "wizard_id": self.id,
                "vehicle_name": line["_vehicle_name"],
                "driver_name": line["_driver_name"],
                "overlap_days": line["_overlap_days"],
                "round_trip_km": line["_round_trip_km"],
                "office_ratio_pct": line["_office_ratio"] * 100,
                "co2_gkm": line["_co2_gkm"],
                "total_km": line["_total_km"],
            }
            for line in lines
        ])
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_generate(self):
        self.ensure_one()
        lines = self._compute_lines()
        if not lines:
            raise UserError(_(
                "No commuting emissions to record for this period.\n"
                "Check that:\n"
                "  • Vehicles have CO₂ Emissions (g/km) set\n"
                "  • Assignment logs exist for this period\n"
                "  • Assigned drivers are linked to an employee with home-work distance set"
            ))
        EsgRecord = self.env["enviro.emission.record"].sudo()
        km_uom = self.env.ref("uom.product_uom_km", raise_if_not_found=False)
        reporting_period = self.env["enviro.reporting.period"].search([
            ("company_id", "=", self.company_id.id),
            ("state", "=", "open"),
            ("date_start", "<=", self.date_end),
            ("date_end", ">=", self.date_end),
        ], limit=1)
        created = self.env["enviro.emission.record"]
        for line in lines:
            existing = EsgRecord.search([
                ("fleet_assignation_log_id", "=", line["fleet_assignation_log_id"]),
                ("fleet_commuting_period_start", "<=", self.date_end),
                ("fleet_commuting_period_end", ">=", self.date_start),
            ], limit=1)
            if existing:
                continue
            created |= EsgRecord.create({
                "name": _(
                    "Fleet Commuting – %(vehicle)s / %(driver)s – %(start)s to %(end)s",
                    vehicle=line["_vehicle_name"],
                    driver=line["_driver_name"],
                    start=str(self.date_start),
                    end=str(self.date_end),
                ),
                "company_id": self.company_id.id,
                "date": self.date_end,
                "source_type": "fleet",
                "quantity": line["_total_km"],
                "uom_id": km_uom.id if km_uom else False,
                "vehicle_co2_gkm": line["_co2_gkm"],
                "fleet_vehicle_id": line["_vehicle_id"],
                "fleet_assignation_log_id": line["fleet_assignation_log_id"],
                "fleet_commuting_period_start": self.date_start,
                "fleet_commuting_period_end": self.date_end,
                "reporting_period_id": reporting_period.id if reporting_period else False,
                "state": "logged",
                "notes": _(
                    "Auto-generated: %(days)d days × %(km).1f km/day × %(ratio).0f%% office × %(co2).0f gCO₂/km",
                    days=line["_overlap_days"],
                    km=line["_round_trip_km"],
                    ratio=line["_office_ratio"] * 100,
                    co2=line["_co2_gkm"],
                ),
            })
        return {
            "type": "ir.actions.act_window",
            "name": _("Commuting Emission Records"),
            "res_model": "enviro.emission.record",
            "view_mode": "list,form",
            "domain": [("id", "in", created.ids)],
            "target": "current",
        }

    def _compute_lines(self) -> list[dict]:
        """Build the list of emission data per assignment log."""
        logs = self.env["fleet.vehicle.assignation.log"].search([
            ("date_start", "<=", self.date_end),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", self.date_start),
        ])
        company = self.company_id
        office_ratio = (company.enviro_weekly_office_days or 5.0) / 7.0
        lines = []
        for log in logs:
            vehicle = log.vehicle_id
            co2_gkm = vehicle.co2
            if not co2_gkm:
                continue
            employee = self.env["hr.employee"].search([
                ("work_contact_id", "=", log.driver_id.id),
                ("company_id", "=", company.id),
            ], limit=1)
            if not employee or not employee.km_home_work:
                continue
            overlap_start = max(log.date_start or self.date_start, self.date_start)
            overlap_end = min(log.date_end or self.date_end, self.date_end)
            overlap_days = (overlap_end - overlap_start).days + 1
            if overlap_days <= 0:
                continue
            round_trip_km = employee.km_home_work * 2
            total_km = overlap_days * round_trip_km * office_ratio
            lines.append({
                "fleet_assignation_log_id": log.id,
                "_vehicle_id": vehicle.id,
                "_vehicle_name": vehicle.name,
                "_driver_name": log.driver_id.name,
                "_overlap_days": overlap_days,
                "_round_trip_km": round_trip_km,
                "_office_ratio": office_ratio,
                "_co2_gkm": co2_gkm,
                "_total_km": total_km,
            })
        return lines


class FleetCommutingWizardLine(models.TransientModel):
    _name = "enviro.fleet.commuting.wizard.line"
    _description = "Enviro Fleet Commuting Wizard Preview Line"

    wizard_id = fields.Many2one("enviro.fleet.commuting.wizard", required=True, ondelete="cascade")
    vehicle_name = fields.Char(string="Vehicle", readonly=True)
    driver_name = fields.Char(string="Driver", readonly=True)
    overlap_days = fields.Integer(string="Days", readonly=True)
    round_trip_km = fields.Float(string="Round Trip (km)", readonly=True)
    office_ratio_pct = fields.Float(string="Office %", readonly=True)
    co2_gkm = fields.Float(string="CO₂ (g/km)", readonly=True)
    total_km = fields.Float(string="Total km", readonly=True)
    co2e_kg = fields.Float(string="kgCO₂e", readonly=True, compute="_compute_co2e")

    @api.depends("total_km", "co2_gkm")
    def _compute_co2e(self):
        for line in self:
            line.co2e_kg = line.total_km * line.co2_gkm / 1000.0
