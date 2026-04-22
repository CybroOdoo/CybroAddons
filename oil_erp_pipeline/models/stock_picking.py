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

class StockPicking(models.Model):
    """
    Extends 'stock.picking' to support pipeline transfers, including
    delivery start/end times and weight-based capacity validation.
    """
    _inherit = "stock.picking"

    carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Pipeline Delivery Method",
        domain="[('is_oil_gas_pipeline', '=', True)]",
        help="Pipeline delivery method used for this internal oil and gas transfer.",
    )
    is_pipeline_transfer = fields.Boolean(
        string="Pipeline Transfer",
        default=False,
        help="Enable this when the oil and gas transfer is performed through a pipeline instead of vehicle transport.",
    )
    pipeline_delivery_start = fields.Datetime(
        string="Delivery Start",
        help="Date and time when pipeline delivery starts.",
    )
    pipeline_delivery_end = fields.Datetime(
        string="Delivery End",
        help="Date and time when pipeline delivery ends.",
    )

    @api.onchange("is_pipeline_transfer")
    def _onchange_is_pipeline_transfer(self):
        """
        Clears the carrier if it's not a pipeline and is_pipeline_transfer is enabled.
        Updates the domain for carrier_id dynamically.
        """
        if self.is_pipeline_transfer and self.carrier_id and not self.carrier_id.is_oil_gas_pipeline:
            self.carrier_id = False
        if self.is_pipeline_transfer:
            return {"domain": {"carrier_id": [("is_oil_gas_pipeline", "=", True)]}}
        return {"domain": {"carrier_id": []}}

    def _get_pipeline_planned_weight(self):
        """
        Calculates the total planned weight of the products being transferred
        via pipeline.
        """
        self.ensure_one()
        total_weight = 0.0
        for move in self.move_ids.filtered(
                lambda m: m.state != "cancel" and m.product_id):
            product_qty_in_product_uom = move.product_uom._compute_quantity(
                move.product_uom_qty,
                move.product_id.uom_id,
            )
            total_weight += product_qty_in_product_uom * move.product_id.weight
        return total_weight

    def _validate_pipeline_configuration(self):
        """
        Validates all pipeline-related constraints:
        - Transfer type (oil/gas)
        - Carrier assignment and type
        - Start/end time logical order
        - Weight vs capacity limit
        """
        for picking in self:
            if not picking.is_pipeline_transfer:
                continue
            if not picking.is_oil_gas_transfer:
                raise ValidationError(
                    _("Pipeline transfer can only be enabled for oil and gas transfers."))
            if not picking.carrier_id:
                raise ValidationError(
                    _("Pipeline delivery method is required for pipeline transfers."))
            if picking.carrier_id and not picking.carrier_id.is_oil_gas_pipeline:
                raise ValidationError(
                    _("Only oil and gas pipeline delivery methods can be used for pipeline transfers."))
            if (
                    picking.pipeline_delivery_start
                    and picking.pipeline_delivery_end
                    and picking.pipeline_delivery_end < picking.pipeline_delivery_start
            ):
                raise ValidationError(
                    _("Pipeline delivery end time must be later than or equal to start time."))
            planned_weight = picking._get_pipeline_planned_weight()
            if (
                    picking.carrier_id
                    and picking.carrier_id.max_weight
                    and planned_weight > picking.carrier_id.max_weight
            ):
                raise ValidationError(
                    _(
                        "Transfer weight %(weight)s exceeds the carrier allowable weight %(max_weight)s."
                    )
                    % {
                        "weight": planned_weight,
                        "max_weight": picking.carrier_id.max_weight,
                    }
                )

    @api.constrains(
        "pipeline_delivery_start",
        "pipeline_delivery_end",
        "is_pipeline_transfer",
        "is_oil_gas_transfer",
        "picking_type_id",
        "carrier_id",
    )
    def _check_pipeline_configuration(self):
        """
        Constraint wrapper for pipeline configuration validation.
        """
        self._validate_pipeline_configuration()

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides create to validate pipeline configuration for new records.
        """
        records = super().create(vals_list)
        records._validate_pipeline_configuration()
        return records

    def write(self, vals):
        """
        Overrides write to re-validate pipeline configuration if relevant fields change.
        """
        res = super().write(vals)
        if {
            "is_pipeline_transfer",
            "is_oil_gas_transfer",
            "picking_type_id",
            "carrier_id",
            "pipeline_delivery_start",
            "pipeline_delivery_end",
            "move_ids",
        } & set(vals):
            self._validate_pipeline_configuration()
        return res

    def button_validate(self):
        """
        Ensures pipeline configuration is valid before the picking is validated.
        """
        self._validate_pipeline_configuration()
        return super().button_validate()
