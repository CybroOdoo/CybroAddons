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
from odoo.exceptions import UserError


class StockPickingDeliveryValidationWizard(models.TransientModel):
    """Captures delivery checks before validating a transfer."""
    _name = "stock.picking.delivery.validation.wizard"
    _description = "Stock Picking Delivery Validation Wizard"

    picking_id = fields.Many2one(
        "stock.picking",
        string="Transfer",
        required=True,
        readonly=True,
        help="Oil and gas transfer being validated.",
    )
    line_ids = fields.One2many(
        "stock.picking.delivery.validation.wizard.line",
        "wizard_id",
        string="Transferred Products",
        help="Enter the actual delivered quantity for each transferred product.",
    )
    delivery_arrival_time = fields.Datetime(
        string="Arrival Time",
        required=True,
        help="Date and time when the vehicle reaches the delivery point for unloading.",
    )
    delivery_start_time = fields.Datetime(
        string="Unloading Start Time",
        required=True,
        help="Date and time when unloading starts at the destination.",
    )
    delivery_end_time = fields.Datetime(
        string="Unloading End Time",
        required=True,
        help="Date and time when unloading is completed.",
    )
    loading_temperature = fields.Float(
        string="Loading Temperature (C)",
        required=True,
        help="Product temperature measured when the transfer was loaded.",
    )
    arrival_temperature = fields.Float(
        string="Arrival Temperature (C)",
        required=True,
        help="Product temperature measured when the transfer reached destination.",
    )
    gross_weight_loaded = fields.Float(
        string="Gross Weight (Loaded)",
        required=True,
        help="Total vehicle weight measured while loaded at delivery validation.",
    )
    gross_weight_empty = fields.Float(
        string="Gross Weight (Empty)",
        required=True,
        help="Vehicle weight measured after unloading or when empty.",
    )
    tank_volume_before = fields.Float(
        string="Tank Volume Before",
        required=True,
        help="Measured destination tank volume before unloading starts.",
    )
    tank_volume_after = fields.Float(
        string="Tank Volume After",
        required=True,
        help="Measured destination tank volume after unloading is completed.",
    )
    actual_qty = fields.Float(
        string="Actual Delivered Qty",
        compute="_compute_actual_qty",
        store=False,
        help="Total actual delivered quantity based on the entered product lines.",
    )
    delivery_status = fields.Selection(
        [
            ("ok", "OK"),
            ("short", "Short Delivery"),
            ("excess", "Excess Delivery"),
            ("damaged", "Damaged"),
        ],
        string="Delivery Status",
        required=True,
        help="Final delivery validation result recorded by the operator.",
    )
    remarks = fields.Text(
        string="Remarks",
        help="Additional delivery notes, discrepancies, or operational comments.",
    )
    base_remarks = fields.Text(
        string="Base Remarks",
        help="Manual remarks entered apart from the product line notes.",
    )

    @api.depends("line_ids.actual_qty")
    def _compute_actual_qty(self):
        """Sum the actual quantities from all wizard lines."""
        for wizard in self:
            wizard.actual_qty = sum(wizard.line_ids.mapped("actual_qty"))

    @api.model
    def default_get(self, fields_list):
        """Prefill the wizard from the selected transfer."""
        res = super().default_get(fields_list)
        picking = self.env["stock.picking"].browse(
            self.env.context.get("default_picking_id"))
        if picking:
            res.update(
                {
                    "picking_id": picking.id,
                    "delivery_arrival_time": picking.delivery_arrival_time,
                    "delivery_start_time": picking.delivery_start_time,
                    "delivery_end_time": picking.delivery_end_time,
                    "loading_temperature": picking.loading_temperature,
                    "arrival_temperature": picking.arrival_temperature,
                    "gross_weight_loaded": picking.gross_weight_loaded,
                    "gross_weight_empty": picking.gross_weight_empty,
                    "tank_volume_before": picking.tank_volume_before,
                    "tank_volume_after": picking.tank_volume_after,
                    "delivery_status": picking.delivery_status,
                    "remarks": picking.remarks,
                    "base_remarks": picking.remarks,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "move_id": move.id,
                                "product_id": move.product_id.id,
                                "planned_qty": move.product_uom_qty,
                                "uom_id": move.product_uom.id,
                                "actual_qty": move.quantity,
                                "remark": False,
                            },
                        )
                        for move in picking.move_ids.filtered(
                            lambda m: m.state not in ("done", "cancel"))
                    ],
                }
            )
        return res

    def _compose_remarks(self):
        """Combine manual remarks with line-level remarks."""
        self.ensure_one()
        line_remarks = [
            f"{line.product_id.display_name} - {line.remark}"
            for line in self.line_ids
            if line.product_id and line.remark
        ]
        return "\n".join(
            filter(None, [self.base_remarks, "\n".join(line_remarks)]))

    @api.onchange("line_ids", "line_ids.product_id", "line_ids.remark",
                  "base_remarks")
    def _onchange_remarks(self):
        """Refresh the remarks field when line notes change."""
        for wizard in self:
            wizard.remarks = wizard._compose_remarks()

    def action_confirm(self):
        """Save delivery details and validate the transfer."""
        self.ensure_one()
        if not self.picking_id:
            raise UserError(_("A transfer is required to continue validation."))
        delivered_qty_by_move = {}
        for line in self.line_ids:
            delivered_qty_by_move[line.move_id.id] = line.actual_qty
        self.picking_id.write(
            {
                "delivery_arrival_time": self.delivery_arrival_time,
                "delivery_start_time": self.delivery_start_time,
                "delivery_end_time": self.delivery_end_time,
                "loading_temperature": self.loading_temperature,
                "arrival_temperature": self.arrival_temperature,
                "gross_weight_loaded": self.gross_weight_loaded,
                "gross_weight_empty": self.gross_weight_empty,
                "tank_volume_before": self.tank_volume_before,
                "tank_volume_after": self.tank_volume_after,
                "actual_qty": self.actual_qty,
                "delivery_status": self.delivery_status,
                "remarks": self.remarks,
            }
        )
        self.picking_id._apply_actual_qty_to_moves(delivered_qty_by_move)
        return self.picking_id.with_context(
            skip_delivery_validation_wizard=True).button_validate()


class StockPickingDeliveryValidationWizardLine(models.TransientModel):
    """Stores delivered quantities for each transfer line."""
    _name = "stock.picking.delivery.validation.wizard.line"
    _description = "Stock Picking Delivery Validation Wizard Line"

    wizard_id = fields.Many2one(
        "stock.picking.delivery.validation.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
        help="Select the wizard.")
    move_id = fields.Many2one(
        "stock.move",
        string="Stock Move",
        required=True,
        readonly=True,
        help="Select the stock Move.")
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        readonly=True,
        help="Select the product.")
    planned_qty = fields.Float(
        string="Planned Qty",
        readonly=True,
        help="Planned quantity from the transfer line.")
    actual_qty = fields.Float(
        string="Actual Delivered Qty",
        required=True,
        help="Actual delivered quantity for this product line.")
    uom_id = fields.Many2one(
        "uom.uom",
        string="UoM",
        readonly=True,
        help="Select the uoM.")
    remark = fields.Text(
        string="Remark",
        help="Remark for this transferred product line.")

    @api.constrains("actual_qty", "planned_qty")
    def _check_actual_qty(self):
        """Prevent negative delivered quantities."""
        for line in self:
            if line.actual_qty < 0:
                raise UserError(
                    _("Actual delivered quantity cannot be negative."))
            # if line.actual_qty > line.planned_qty:
            #     raise UserError(_("Actual delivered quantity cannot exceed planned quantity for a product line."))
