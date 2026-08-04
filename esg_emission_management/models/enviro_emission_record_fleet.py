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


class EnviroEmissionRecord(models.Model):
    """Adds fleet traceability fields and vehicle CO₂ calculation to emission records."""
    _inherit = "enviro.emission.record"

    fleet_vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Fleet Vehicle",
        index=True,
        tracking=True,
    )
    fleet_employee_id = fields.Many2one(
        "hr.employee",
        string="Driver (Employee)",
        compute="_compute_fleet_employee",
        store=True,
        readonly=True,
        index=True,
    )

    @api.depends("fleet_assignation_log_id")
    def _compute_fleet_employee(self):
        for record in self:
            if record.fleet_assignation_log_id:
                driver = record.fleet_assignation_log_id.driver_id
                record.fleet_employee_id = self.env["hr.employee"].search(
                    [("work_contact_id", "=", driver.id)], limit=1
                )
            else:
                record.fleet_employee_id = False

    @api.onchange("fleet_vehicle_id")
    def _onchange_fleet_vehicle(self):
        for record in self:
            if record.fleet_vehicle_id:
                record.vehicle_co2_gkm = record.fleet_vehicle_id.co2
                km_uom = self.env.ref("uom.product_uom_km", raise_if_not_found=False)
                if km_uom:
                    record.uom_id = km_uom

    fleet_assignation_log_id = fields.Many2one(
        "fleet.vehicle.assignation.log",
        string="Fleet Assignment",
        copy=False,
        readonly=True,
        index=True,
    )
    fleet_commuting_period_start = fields.Date(
        string="Commuting Period Start",
        readonly=True,
        copy=False,
    )
    fleet_commuting_period_end = fields.Date(
        string="Commuting Period End",
        readonly=True,
        copy=False,
    )
    fleet_odometer_id = fields.Many2one(
        "fleet.vehicle.odometer",
        string="Odometer Reading",
        copy=False,
        readonly=True,
        index=True,
    )
    vehicle_co2_gkm = fields.Float(
        string="Vehicle CO₂ (g/km)",
        help="Manufacturer CO₂ spec (gCO₂/km). Auto-filled from the vehicle; can be overridden.",
    )

    @api.depends(
        "factor_id", "factor_id.kg_co2e_per_unit", "factor_id.uncertainty_pct",
        "factor_id.calculation_type", "factor_id.uom_id", "factor_id.currency_id",
        "quantity", "uom_id", "amount", "currency_id",
        "vehicle_co2_gkm",
    )
    def _compute_emissions(self):
        super()._compute_emissions()
        for entry in self:
            if not entry.factor_id and entry.vehicle_co2_gkm and entry.quantity:
                # gCO₂/km × km ÷ 1000 = kgCO₂e
                entry.co2e_kg = entry.quantity * entry.vehicle_co2_gkm / 1000.0
                entry.co2e_tonnes = entry.co2e_kg / 1000.0
                entry.uncertainty_kg = 0.0

    def action_log(self):
        for entry in self:
            if not entry.factor_id and entry.vehicle_co2_gkm:
                entry.state = "logged"
            else:
                entry.state = "logged" if entry.factor_id else "missing"
