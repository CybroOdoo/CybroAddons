# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    """
    Extends 'fleet.vehicle' to support oil and gas transport operations. 
    Tracks tank capacity, tare weight, and allowable payload for road safety 
    and logistics planning.
    """
    _inherit = "fleet.vehicle"

    transfer_count = fields.Integer(
        string="Transfers",
        compute="_compute_transfer_count",
        help="Number of oil and gas internal transfers linked to this vehicle.")
    is_oil_gas_fleet = fields.Boolean(
        string="Oil and Gas Fleet",
        default=False,
        help="Enable this vehicle for oil and gas transport operations managed by this module.")
    tank_capacity = fields.Float(
        string="Tank Capacity",
        help="Maximum fluid volume that the vehicle tank can safely carry.")
    tare_weight = fields.Float(
        string="Tare Weight",
        help="Empty vehicle weight before loading any product.")
    max_gross_weight = fields.Float(
        string="Max Gross Weight",
        help="Maximum legal road weight for the loaded vehicle.")
    allowable_payload = fields.Float(
        string="Allowable Payload",
        compute="_compute_allowable_payload",
        store=True,
        help="Maximum net load allowed inside the vehicle, calculated as max gross weight minus tare weight.")
    is_available = fields.Boolean(
        string="Is Available",
        default=True,
        help="Enable this to make the vehicle selectable for oil and gas transfer assignments.",)

    @api.depends("max_gross_weight", "tare_weight")
    def _compute_allowable_payload(self):
        """
        Calculates the maximum net payload allowed for the vehicle (Gross - Tare).
        """
        for vehicle in self:
            vehicle.allowable_payload = max(
                vehicle.max_gross_weight - vehicle.tare_weight, 0.0)

    def _compute_transfer_count(self):
        """
        Computes the total number of internal oil and gas transfers assigned 
        to this vehicle.
        """
        grouped_data = self.env["stock.picking"]._read_group(
            [
                ("vehicle_id", "in", self.ids),
                ("is_oil_gas_transfer", "=", True),
                ("picking_type_code", "=", "internal"),
            ],
            ["vehicle_id"],
            ["__count"],
        )
        counts = {vehicle.id: count for vehicle, count in grouped_data}
        for vehicle in self:
            vehicle.transfer_count = counts.get(vehicle.id, 0)

    def action_view_transfers(self):
        """
        Returns an action to open a list view of all internal oil and gas 
        transfers linked to this vehicle.
        """
        self.ensure_one()
        action = \
        self.env.ref("oil_erp_transfers.action_oil_gas_transfer").sudo().read()[
            0]
        action["domain"] = [
            ("vehicle_id", "=", self.id),
            ("is_oil_gas_transfer", "=", True),
            ("picking_type_code", "=", "internal"),
        ]
        action["context"] = {
            "contact_display": "partner_address",
            "restricted_picking_type_code": "internal",
            "default_is_oil_gas_transfer": 1,
            "default_vehicle_id": self.id,
            "search_default_internal": 1,
        }
        return action

    @api.constrains("tank_capacity", "tare_weight", "max_gross_weight")
    def _check_oil_gas_vehicle_values(self):
        """
        Validates vehicle capacity and weight configuration for oil and gas fleet.
        """
        for vehicle in self:
            if not vehicle.is_oil_gas_fleet:
                continue
            if vehicle.tank_capacity < 0:
                raise ValidationError(_("Tank capacity cannot be negative."))
            if vehicle.tare_weight < 0:
                raise ValidationError(_("Tare weight cannot be negative."))
            if vehicle.max_gross_weight < 0:
                raise ValidationError(_("Max gross weight cannot be negative."))
            if vehicle.max_gross_weight and vehicle.max_gross_weight < vehicle.tare_weight:
                raise ValidationError(
                    _("Max gross weight must be greater than or equal to tare weight."))
