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
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    """
    Extends 'stock.picking' to handle complex internal oil and gas transfers. 
    Supports temperature recording, gravity-based volume calculations, vehicle 
    payload validation, and detailed delivery measurement tracking.
    """
    _inherit = "stock.picking"

    product_type = fields.Selection(
        selection=[
            ("crude_oil", "Crude Oil"),
            ("gas_condensation", "Gas Condensation"),
            ("produced_water", "Produced Water"),
            ("refinery_product", "Refinery Product"),
            ("natural_gas_liquid", "Natural Gas Liquid"),
            ("other", "Other"),
        ],
        string="Product Type",
        help="Classifies the material being moved through the internal transfer.",
    )
    is_oil_gas_transfer = fields.Boolean(
        string="Oil and Gas Transfer",
        default=False,
        help="Enable this transfer to use the oil and gas transport controls added by this module.",
    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        domain="[('is_oil_gas_fleet', '=', True), ('is_available', '=', True)]",
        help="Vehicle assigned to transport the internal transfer load.",
    )
    driver_id = fields.Many2one(
        "hr.employee",
        string="Driver",
        domain="[('company_id', 'in', [False, company_id])]",
        help="Driver responsible for the transfer. It is autofilled from the assigned vehicle and can still be changed.",
    )
    temperature_f = fields.Float(
        string="Temperature (F)",
        help="Recorded product temperature in degrees Fahrenheit at transfer time.",
    )
    loading_temperature = fields.Float(
        string="Loading Temperature (C)",
        help="Product temperature measured when the transfer was loaded.",
    )
    arrival_temperature = fields.Float(
        string="Arrival Temperature (C)",
        help="Product temperature measured when the transfer reached destination.",
    )
    temperature_difference = fields.Float(
        string="Temperature Difference",
        compute="_compute_temperature_difference",
        store=True,
        help="Difference between arrival temperature and loading temperature.",
    )
    net_weight = fields.Float(
        string="Net Weight",
        compute="_compute_net_weight",
        store=True,
        help="Actual product weight loaded in the vehicle. It cannot exceed the vehicle allowable payload.",
    )
    gross_weight_loaded = fields.Float(
        string="Gross Weight (Loaded)",
        help="Total vehicle weight measured while loaded at delivery validation.",
    )
    gross_weight_empty = fields.Float(
        string="Gross Weight (Empty)",
        help="Vehicle weight measured after unloading or when empty.",
    )
    departure_time = fields.Datetime(
        string="Departure Time",
        help="Date and time when the vehicle leaves the source location.",
    )
    arrival_time = fields.Datetime(
        string="Arrival Time",
        help="Date and time when the vehicle arrives at the destination location.",
    )
    delivery_arrival_time = fields.Datetime(
        string="Arrival Time",
        help="Date and time when the vehicle reaches the delivery point for unloading.",
    )
    delivery_start_time = fields.Datetime(
        string="Unloading Start Time",
        help="Date and time when unloading starts at the destination.",
    )
    delivery_end_time = fields.Datetime(
        string="Unloading End Time",
        help="Date and time when unloading is completed.",
    )
    delivery_duration = fields.Float(
        string="Unloading Duration (hrs)",
        compute="_compute_delivery_duration",
        store=True,
        help="Total unloading duration in hours, based on unloading start and end times.",
    )
    tank_volume_before = fields.Float(
        string="Tank Volume Before",
        help="Measured destination tank volume before unloading starts.",
    )
    tank_volume_after = fields.Float(
        string="Tank Volume After",
        help="Measured destination tank volume after unloading is completed.",
    )
    delivered_volume = fields.Float(
        string="Delivered Volume",
        compute="_compute_delivered_volume",
        store=True,
        help="Delivered volume calculated from the difference between tank volume after and before unloading.",
    )
    planned_qty = fields.Float(
        string="Planned Quantity",
        compute="_compute_planned_qty",
        store=True,
        help="Total planned quantity from the transfer stock moves.",
    )
    actual_qty = fields.Float(
        string="Actual Delivered Qty",
        help="Actual delivered quantity confirmed at destination.",
    )
    quantity_loss = fields.Float(
        string="Loss / Difference",
        compute="_compute_quantity_loss",
        store=True,
        help="Difference between planned quantity and actual delivered quantity.",
    )
    delivery_status = fields.Selection(
        [
            ("ok", "OK"),
            ("short", "Short Delivery"),
            ("excess", "Excess Delivery"),
            ("damaged", "Damaged"),
        ],
        string="Delivery Status",
        help="Final delivery validation result recorded by the operator.",
    )
    remarks = fields.Text(
        string="Remarks",
        help="Additional delivery notes, discrepancies, or operational comments.",
    )
    vehicle_allowable_payload = fields.Float(
        string="Vehicle Allowable Payload",
        related="vehicle_id.allowable_payload",
        readonly=True,
        help="Available legal payload capacity of the assigned vehicle.",
    )
    vehicle_tank_capacity = fields.Float(
        string="Vehicle Tank Capacity",
        related="vehicle_id.tank_capacity",
        readonly=True,
        help="Tank capacity of the assigned vehicle for quick reference during dispatch.",
    )

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        """
        Automatically assigns the driver from the selected vehicle's driver or
        associated employee.
        """
        for picking in self:
            if not picking.vehicle_id:
                continue
            employee = picking.vehicle_id.driver_employee_id
            if not employee and picking.vehicle_id.driver_id:
                employee = self.env["hr.employee"].search(
                    [("work_contact_id", "=", picking.vehicle_id.driver_id.id)],
                    limit=1,
                )
            if employee:
                picking.driver_id = employee

    def _open_delivery_validation_wizard(self):
        """
        Internal helper to open the delivery measurements recording wizard.
        """
        self.ensure_one()
        return {
            "name": _("Delivery Validation"),
            "type": "ir.actions.act_window",
            "res_model": "stock.picking.delivery.validation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_picking_id": self.id,
                "button_validate_picking_ids": self.env.context.get("button_validate_picking_ids", self.ids),
            },
        }

    def _apply_actual_qty_to_moves(self, delivered_qty_by_move=None):
        """
        Updates stock move quantities with the actual measured quantities
        recorded during delivery validation.
        """
        for picking in self:
            moves = picking.move_ids.filtered(
                lambda move: move.state not in ("done", "cancel"))
            if not moves:
                continue

            delivered_qty_by_move = delivered_qty_by_move or {}
            for move in moves:
                move.quantity = delivered_qty_by_move.get(move.id, 0.0)

    def button_validate(self):
        """
        Overridden to enforce delivery validation wizard for oil and gas transfers.
        """
        oil_gas_pickings = self.filtered(
            lambda p: p.is_oil_gas_transfer and p.state not in ("done", "cancel")
        )
        if oil_gas_pickings and not self.env.context.get("skip_delivery_validation_wizard"):
            if len(self) > 1:
                raise UserError(
                    _("Validate oil and gas transfers one at a time so delivery measurements can be recorded."))
            return oil_gas_pickings._open_delivery_validation_wizard()
        return super().button_validate()

    @api.depends("arrival_temperature", "loading_temperature")
    def _compute_temperature_difference(self):
        """
        Calculates the change in temperature during transport.
        """
        for picking in self:
            picking.temperature_difference = picking.arrival_temperature - picking.loading_temperature

    @api.depends("gross_weight_loaded", "gross_weight_empty")
    def _compute_net_weight(self):
        """
        Calculates the net product weight (Loaded - Empty).
        """
        for picking in self:
            picking.net_weight = picking.gross_weight_loaded - picking.gross_weight_empty

    @api.depends("delivery_start_time", "delivery_end_time")
    def _compute_delivery_duration(self):
        """
        Calculates the duration of the unloading process in hours.
        """
        for picking in self:
            if picking.delivery_start_time and picking.delivery_end_time:
                picking.delivery_duration = (
                                                    picking.delivery_end_time - picking.delivery_start_time
                                            ).total_seconds() / 3600
            else:
                picking.delivery_duration = 0.0

    @api.depends("tank_volume_before", "tank_volume_after")
    def _compute_delivered_volume(self):
        """
        Calculates delivered volume from tank level changes at destination.
        """
        for picking in self:
            picking.delivered_volume = picking.tank_volume_after - picking.tank_volume_before

    @api.depends("move_ids.product_uom_qty")
    def _compute_planned_qty(self):
        """
        Aggregates total planned quantity from stock moves.
        """
        for picking in self:
            picking.planned_qty = sum(picking.move_ids.mapped("product_uom_qty"))

    @api.depends("planned_qty", "actual_qty")
    def _compute_quantity_loss(self):
        """
        Calculates the difference between planned and actual delivered quantity.
        """
        for picking in self:
            picking.quantity_loss = picking.planned_qty - picking.actual_qty

    # @api.constrains("picking_type_id", "is_oil_gas_transfer", "vehicle_id")
    # def _check_internal_transfer_vehicle(self):
    #     for picking in self:
    #
    #         if not picking.is_oil_gas_transfer:
    #             continue
    #         if picking.picking_type_id.code != "internal":
    #             raise ValidationError(_("Oil and gas transfers must use an internal transfer operation type."))
    #         if not picking.product_type:
    #             raise ValidationError(_("Product type is required for oil and gas transfers."))
    #         if not picking.vehicle_id:
    #             raise ValidationError(_("Vehicle is required for oil and gas transfers."))
    #         if not picking.driver_id:
    #             raise ValidationError(_("Driver is required for oil and gas transfers."))
    #         if picking.vehicle_id and not picking.vehicle_id.is_oil_gas_fleet:
    #             raise ValidationError(_("The selected vehicle must be marked as an oil and gas fleet vehicle."))
    #         if picking.vehicle_id and not picking.vehicle_id.is_available:
    #             raise ValidationError(_("The selected vehicle is not available for transfer assignment."))

    @api.constrains("net_weight", "vehicle_id", "is_oil_gas_transfer")
    def _check_net_weight(self):
        """
        Validates that net weight is positive and within vehicle payload limits.
        """
        for picking in self:
            if not picking.is_oil_gas_transfer:
                continue
            if picking.net_weight < 0:
                raise ValidationError(_("Net weight cannot be negative."))
            if picking.vehicle_id and picking.net_weight > picking.vehicle_id.allowable_payload:
                raise ValidationError(_("Net weight cannot exceed the vehicle allowable payload."))

    @api.constrains("departure_time", "arrival_time", "is_oil_gas_transfer")
    def _check_transfer_times(self):
        """
        Ensures arrival time is not before departure time.
        """
        for picking in self:
            if not picking.is_oil_gas_transfer:
                continue
            if picking.departure_time and picking.arrival_time and picking.arrival_time < picking.departure_time:
                raise ValidationError(_("Arrival time must be later than or equal to departure time."))

    @api.constrains("delivery_arrival_time", "delivery_start_time",
                    "delivery_end_time", "is_oil_gas_transfer")
    def _check_delivery_times(self):
        """
        Validates logical sequence of unloading process timestamps.
        """
        for picking in self:
            if not picking.is_oil_gas_transfer:
                continue
            if (
                    picking.delivery_arrival_time
                    and picking.delivery_start_time
                    and picking.delivery_start_time < picking.delivery_arrival_time
            ):
                raise ValidationError(
                    _("Unloading start time must be later than or equal to delivery arrival time."))
            if (
                    picking.delivery_start_time
                    and picking.delivery_end_time
                    and picking.delivery_end_time < picking.delivery_start_time
            ):
                raise ValidationError(
                    _("Unloading end time must be later than or equal to unloading start time."))

    @api.constrains(
        "gross_weight_loaded",
        "gross_weight_empty",
        "tank_volume_before",
        "tank_volume_after",
        "actual_qty",
        "is_oil_gas_transfer",
    )
    def _check_delivery_measurements(self):
        """
        Performs logical validation on all physical delivery measurements.
        """
        for picking in self:
            if not picking.is_oil_gas_transfer:
                continue
            if picking.gross_weight_loaded < 0 or picking.gross_weight_empty < 0:
                raise ValidationError(_("Gross weights cannot be negative."))
            if picking.gross_weight_loaded and picking.gross_weight_loaded < picking.gross_weight_empty:
                raise ValidationError(
                    _("Loaded gross weight must be greater than or equal to empty gross weight."))
            if picking.tank_volume_before < 0 or picking.tank_volume_after < 0:
                raise ValidationError(
                    _("Tank volume measurements cannot be negative."))
            if picking.actual_qty < 0:
                raise ValidationError(
                    _("Actual delivered quantity cannot be negative."))
