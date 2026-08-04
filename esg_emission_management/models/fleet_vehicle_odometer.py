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

_MILES_TO_KM = 1.60934


class FleetVehicleOdometer(models.Model):
    _inherit = "fleet.vehicle.odometer"

    enviro_emission_record_id = fields.Many2one(
        "enviro.emission.record",
        string="Enviro Emission Record",
        copy=False,
        readonly=True,
    )

    def _get_distance_km(self) -> float:
        """Return km traveled since the previous odometer reading for this vehicle."""
        prev = self.env["fleet.vehicle.odometer"].search([
            ("vehicle_id", "=", self.vehicle_id.id),
            ("id", "!=", self.id),
            ("value", "<", self.value),
        ], order="value desc", limit=1)
        if not prev:
            return 0.0
        delta = self.value - prev.value
        if self.vehicle_id.odometer_unit == "mi":
            delta *= _MILES_TO_KM
        return delta

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_enviro_emission_record()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(f in vals for f in ("value", "date", "vehicle_id")):
            self._sync_enviro_emission_record()
        return result

    @api.model
    def _cron_sync_odometer_records(self) -> None:
        cutoff = fields.Date.today() - timedelta(days=30)
        missing = self.search([
            ("enviro_emission_record_id", "=", False),
            ("date", ">=", cutoff),
        ])
        missing._sync_enviro_emission_record()

    def _sync_enviro_emission_record(self) -> None:
        EsgRecord = self.env["enviro.emission.record"].sudo()
        km_uom = self.env.ref("uom.product_uom_km", raise_if_not_found=False)
        for odometer in self:
            vehicle = odometer.vehicle_id
            if not vehicle:
                continue
            co2_gkm = vehicle.co2
            if not co2_gkm:
                continue
            distance_km = odometer._get_distance_km()
            if distance_km <= 0.0:
                continue
            company = vehicle.company_id or self.env.company
            vals = {
                "name": _(
                    "Fleet Travel – %(vehicle)s – %(date)s",
                    vehicle=vehicle.name,
                    date=str(odometer.date or fields.Date.context_today(self)),
                ),
                "company_id": company.id,
                "date": odometer.date or fields.Date.context_today(self),
                "source_type": "fleet",
                "quantity": distance_km,
                "uom_id": km_uom.id if km_uom else False,
                "vehicle_co2_gkm": co2_gkm,
                "fleet_vehicle_id": vehicle.id,
                "state": "logged",
                "fleet_odometer_id": odometer.id,
                "notes": _(
                    "Auto-generated from odometer reading (vehicle: %(v)s, %(km).1f km, %(co2).1f gCO₂/km).",
                    v=vehicle.name,
                    km=distance_km,
                    co2=co2_gkm,
                ),
            }
            if odometer.enviro_emission_record_id:
                odometer.enviro_emission_record_id.write(vals)
            else:
                record = EsgRecord.create(vals)
                odometer.enviro_emission_record_id = record.id
