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


class OilGatePassCreateWizard(models.TransientModel):
    """
    Wizard for creating a gate pass based on data from a stock picking record.
    Initializes fields like products, partner, and locations automatically.
    """
    _name = "oil.gate.pass.create.wizard"
    _description = "Create Gate Pass Wizard"

    picking_id = fields.Many2one("stock.picking", string="Picking",
                                 required=True, readonly=True,
                                 help="Select the picking.")
    date = fields.Datetime(string="Date", required=True,
                           default=fields.Datetime.now,
                           help="Select the date and time for date.")
    gate_pass_type = fields.Selection(
        [("in", "Inward"), ("out", "Outward"), ("internal", "Internal")],
        string="Gate Pass Type",
        required=True,
        help="Choose the gate Pass Type.")
    partner_id = fields.Many2one("res.partner", string="Partner",
                                 help="Select the partner.")
    driver_name = fields.Char(string="Driver Name",
                              help="Enter the driver Name.")
    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle",
                                 help="Select the vehicle.")
    vehicle_number = fields.Char(string="Vehicle Number",
                                 help="Enter the vehicle Number.")
    transporter_id = fields.Many2one("res.partner", string="Transporter",
                                     help="Select the transporter.")
    line_ids = fields.One2many("oil.gate.pass.create.wizard.line", "wizard_id",
                               string="Products", help="Lists the products.")
    quantity = fields.Float(string="Quantity", compute="_compute_totals",
                            store=False, help="Enter the quantity.")
    uom_id = fields.Many2one("uom.uom", string="UoM", compute="_compute_totals",
                             store=False, help="Select the uoM.")
    source_location_id = fields.Many2one("stock.location",
                                         string="Source Location",
                                         help="Select the source Location.")
    destination_location_id = fields.Many2one("stock.location",
                                              string="Destination Location",
                                              help="Select the destination Location.")
    density = fields.Float(string="Density", help="Enter the density.")
    temperature = fields.Float(string="Temperature",
                               help="Enter the temperature.")
    pressure = fields.Float(string="Pressure", help="Enter the pressure.")
    gross_qty = fields.Float(string="Gross Qty", help="Enter the gross Qty.")
    net_qty = fields.Float(string="Net Qty", help="Enter the net Qty.")
    loss_qty = fields.Float(string="Loss Qty", compute="_compute_loss_qty",
                            store=False, help="Enter the loss Qty.")
    gate_in_time = fields.Datetime(string="Gate In Time",
                                   help="Select the date and time for gate In Time.")
    gate_out_time = fields.Datetime(string="Gate Out Time",
                                    help="Select the date and time for gate Out Time.")
    remarks = fields.Text(string="Remarks", help="Enter the remarks.")
    sale_order_id = fields.Many2one("sale.order", string="Sale Order",
                                    help="Select the sale Order.")
    purchase_order_id = fields.Many2one("purchase.order",
                                        string="Purchase Order",
                                        help="Select the purchase Order.")
    security_check = fields.Boolean(string="Security Inspection Completed",
                                    help="Enable this when security Inspection Completed applies.")

    @api.model
    def default_get(self, field_list):
        """Pre-populates the wizard with data from the active picking record."""
        res = super().default_get(field_list)
        picking = self.env["stock.picking"].browse(
            self.env.context.get("default_picking_id"))
        if not picking:
            return res
        driver_name = False
        if "driver_id" in picking._fields and picking.driver_id:
            driver_name = picking.driver_id.name
        elif "vehicle_id" in picking._fields and picking.vehicle_id and picking.vehicle_id.driver_id:
            driver_name = picking.vehicle_id.driver_id.name
        transporter = False
        if "carrier_id" in picking._fields and picking.carrier_id:
            transporter = getattr(picking.carrier_id, "partner_id", False)
        gate_pass_type = {
            "incoming": "in",
            "outgoing": "out",
            "internal": "internal",
        }.get(picking.picking_type_code, "internal")
        line_commands = []
        for move in picking.move_ids.filtered(
                lambda move: move.state != "cancel" and move.product_id):
            line_commands.append(
                (0, 0, {
                    "product_id": move.product_id.id,
                    "quantity": move.product_uom_qty,
                    "uom_id": move.product_uom.id
                },
                 )
            )
        res.update(
            {
                "picking_id": picking.id,
                "gate_pass_type": gate_pass_type,
                "partner_id": picking.partner_id.id,
                "driver_name": driver_name,
                "vehicle_id": picking.vehicle_id.id if "vehicle_id" in picking._fields else False,
                "vehicle_number": (
                        picking.vehicle_id.license_plate or picking.vehicle_id.name
                ) if "vehicle_id" in picking._fields and picking.vehicle_id else False,
                "transporter_id": transporter.id if transporter else False,
                "line_ids": line_commands,
                "source_location_id": picking.location_id.id,
                "destination_location_id": picking.location_dest_id.id,
                "sale_order_id": picking.sale_id.id if "sale_id" in picking._fields and picking.sale_id else False,
                "purchase_order_id": (
                    picking.purchase_id.id if "purchase_id" in picking._fields and picking.purchase_id else False
                ),
                "remarks": picking.note,
            }
        )
        return res

    @api.depends("line_ids.quantity", "line_ids.uom_id")
    def _compute_totals(self):
        """
        Computes the total quantity and determines the common UoM for the
        wizard lines.
        """
        for wizard in self:
            wizard.quantity = sum(wizard.line_ids.mapped("quantity"))
            uoms = wizard.line_ids.mapped("uom_id")
            wizard.uom_id = uoms[0] if len(uoms) == 1 else False

    @api.depends("gross_qty", "net_qty")
    def _compute_loss_qty(self):
        """Calculates loss quantity as gross minus net quantity."""
        for wizard in self:
            wizard.loss_qty = wizard.gross_qty - wizard.net_qty

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        """Fill vehicle details when a vehicle is selected."""
        for wizard in self:
            wizard.vehicle_number = wizard.vehicle_id.license_plate or wizard.vehicle_id.name or False
            if wizard.vehicle_id and not wizard.driver_name and wizard.vehicle_id.driver_id:
                wizard.driver_name = wizard.vehicle_id.driver_id.name

    def action_create_gate_pass(self):
        """Creates the 'oil.gate.pass' record and its lines based on wizard inputs."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(
                _("Add at least one product line before creating the gate pass."))
        gate_pass = self.env["oil.gate.pass"].create(
            {
                "date": self.date,
                "gate_pass_type": self.gate_pass_type,
                "partner_id": self.partner_id.id,
                "driver_name": self.driver_name,
                "vehicle_id": self.vehicle_id.id,
                "vehicle_number": self.vehicle_number,
                "transporter_id": self.transporter_id.id,
                "source_location_id": self.source_location_id.id,
                "destination_location_id": self.destination_location_id.id,
                "density": self.density,
                "temperature": self.temperature,
                "pressure": self.pressure,
                "gross_qty": self.gross_qty,
                "net_qty": self.net_qty,
                "gate_in_time": self.gate_in_time,
                "gate_out_time": self.gate_out_time,
                "remarks": self.remarks,
                "picking_id": self.picking_id.id,
                "sale_order_id": self.sale_order_id.id,
                "purchase_order_id": self.purchase_order_id.id,
                "security_check": self.security_check,
                "product_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "quantity": line.quantity,
                            "uom_id": line.uom_id.id,
                        },
                    )
                    for line in self.line_ids
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Gate Pass"),
            "res_model": "oil.gate.pass",
            "res_id": gate_pass.id,
            "view_mode": "form",
            "target": "current",
        }


class OilGatePassCreateWizardLine(models.TransientModel):
    """Line items for the gate pass creation wizard."""
    _name = "oil.gate.pass.create.wizard.line"
    _description = "Create Gate Pass Wizard Line"

    wizard_id = fields.Many2one(
        "oil.gate.pass.create.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
        help="Select the wizard.")
    product_id = fields.Many2one("product.product", string="Product",
                                 required=True, help="Select the product.")
    quantity = fields.Float(string="Quantity", required=True, default=1.0,
                            help="Enter the quantity.")
    uom_id = fields.Many2one("uom.uom", string="UoM", required=True,
                             help="Select the uoM.")
