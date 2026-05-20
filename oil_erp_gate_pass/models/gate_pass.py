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
from odoo.orm.table_objects import Constraint
from odoo.exceptions import ValidationError

from odoo.tools.translate import _


class OilGatePass(models.Model):
    """
    Model for managing gate passes (Inward, Outward, Internal) within oil facilities.
    Tracks vehicle information, driver details, products, and physical parameters
    like density, temperature, and pressure.
    """
    _name = "oil.gate.pass"
    _description = "Oil Gate Pass"
    _order = "date desc, id desc"
    _name_unique = Constraint(
        "UNIQUE(name)",
        "The Gate Pass reference must be unique!"
    )


    name = fields.Char(string="Name", required=True, copy=False, default=lambda self: _("New"))
    date = fields.Datetime(string="Date", required=True, default=fields.Datetime.now)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        help="Current workflow status of this gate pass.")
    gate_pass_type = fields.Selection(
        [("in", "Inward"), ("out", "Outward"), ("internal", "Internal")],
        string="Gate Pass Type",
        required=True,
        help="Direction of material movement: inward, outward, or internal.")
    partner_id = fields.Many2one("res.partner", string="Partner",
                                 help="Business partner associated with this gate pass.")
    driver_name = fields.Char(string="Driver Name",
                              help="Name of the driver operating the vehicle.")
    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle",
                                 help="Fleet vehicle assigned to this gate pass.")
    vehicle_number = fields.Char(string="Vehicle Number",
                                 help="License plate or registration number of the vehicle.")
    transporter_id = fields.Many2one("res.partner", string="Transporter",
                                     help="Transport company responsible for the shipment.")
    product_line_ids = fields.One2many("oil.gate.pass.line", "gate_pass_id",
                                       string="Products", copy=True,
                                       help="Lists the products.")
    product_ids = fields.Many2many("product.product", string="Products",
                                   compute="_compute_product_ids", store=False,
                                   help="Lists the products.")
    quantity = fields.Float(string="Quantity", compute="_compute_totals",
                            store=True, help="Enter the quantity.")
    uom_id = fields.Many2one("uom.uom", string="UoM", compute="_compute_totals",
                             store=True, help="Select the uoM.")
    source_location_id = fields.Many2one("stock.location",
                                         string="Source Location",
                                         help="Select the source Location.")
    destination_location_id = fields.Many2one("stock.location",
                                              string="Destination Location",
                                              help="Select the destination Location.")
    density = fields.Float(string="Density", help="Product density measurement at the time of transfer.")
    temperature = fields.Float(string="Temperature",
                               help="Product temperature at the time of transfer.")
    pressure = fields.Float(string="Pressure", help="Product pressure reading at the time of transfer.")
    gross_qty = fields.Float(string="Gross Qty", help="Total quantity including container or vehicle weight.")
    net_qty = fields.Float(string="Net Qty", help="Actual product quantity after deducting tare.")
    loss_qty = fields.Float(string="Loss Qty", compute="_compute_loss_qty",
                            store=True, help="Enter the loss Qty.")
    gate_in_time = fields.Datetime(string="Gate In Time",
                                   help="Select the date and time for gate In Time.")
    gate_out_time = fields.Datetime(string="Gate Out Time",
                                    help="Select the date and time for gate Out Time.")
    remarks = fields.Text(string="Remarks", help="Additional notes or observations about this gate pass.")
    picking_id = fields.Many2one("stock.picking", string="Picking",
                                 help="Select the picking.")
    sale_order_id = fields.Many2one("sale.order", string="Sale Order",
                                    help="Select the sale Order.")
    purchase_order_id = fields.Many2one("purchase.order",
                                        string="Purchase Order",
                                        help="Select the purchase Order.")
    approved_by = fields.Many2one("res.users", string="Approved By",
                                  readonly=True, help="Select the approved By.")
    approval_date = fields.Datetime(string="Approval Date", readonly=True,
                                    help="Select the date and time for approval Date.")
    security_check = fields.Boolean(string="Security Inspection Completed",
                                    help="Indicates that the security inspection has been completed.")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        help="Select the company.")

    @api.constrains("gate_in_time", "gate_out_time")
    def _check_times(self):
        """
        Validates that gate out time is not earlier than gate in time.
        """
        for rec in self:
            if rec.gate_in_time and rec.gate_out_time and rec.gate_out_time < rec.gate_in_time:
                raise ValidationError(
                    _("Gate Out Time must be later than Gate In Time."))

    @api.depends("product_line_ids.product_id")
    def _compute_product_ids(self):
        """
        Computes a many2many field of products based on the gate pass lines.
        """
        for gate_pass in self:
            gate_pass.product_ids = gate_pass.product_line_ids.mapped("product_id")

    @api.depends("product_line_ids.quantity", "product_line_ids.uom_id")
    def _compute_totals(self):
        """
        Calculates the total quantity and determines the common UoM if applicable.
        """
        for gate_pass in self:
            gate_pass.quantity = sum(
                gate_pass.product_line_ids.mapped("quantity"))
            uoms = gate_pass.product_line_ids.mapped("uom_id")
            gate_pass.uom_id = uoms[0] if len(uoms) == 1 else False

    @api.depends("gross_qty", "net_qty")
    def _compute_loss_qty(self):
        """
        Calculates the loss quantity as the difference between gross and net quantities.
        """
        for gate_pass in self:
            gate_pass.loss_qty = gate_pass.gross_qty - gate_pass.net_qty

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        """
        Autopopulates vehicle number and driver name based on the selected vehicle.
        """
        for gate_pass in self:
            gate_pass.vehicle_number = gate_pass.vehicle_id.license_plate or gate_pass.vehicle_id.name or False
            if not gate_pass.driver_name and gate_pass.vehicle_id.driver_id:
                gate_pass.driver_name = gate_pass.vehicle_id.driver_id.name

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assigns a unique sequence number to new gate pass records.
        """
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "oil.gate.pass") or _("New")
        return super().create(vals_list)

    def action_approve(self):
        """
        Approves the gate pass and records the approver and date.
        """
        for gate_pass in self:
            gate_pass.write(
                {
                    "state": "approved",
                    "approved_by": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                }
            )

    def action_start(self):
        """Set the record state to 'in progress'."""
        self.write({"state": "in_progress"})

    def action_done(self):
        """Set the record state to 'done'."""
        self.write({"state": "done"})

    def action_cancel(self):
        """Set the record state to 'cancel'."""
        self.write({"state": "cancel"})

    def action_reset_draft(self):
        """Reset the gate pass back to draft state."""
        self.write({"state": "draft"})

    def action_view_picking(self):
        """Returns an action to view the linked stock picking record."""
        self.ensure_one()
        if not self.picking_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Picking"),
            "res_model": "stock.picking",
            "res_id": self.picking_id.id,
            "view_mode": "form",
            "target": "current",
        }


class OilGatePassLine(models.Model):
    """Line items for a gate pass, specifying the product, quantity, and UoM."""
    _name = "oil.gate.pass.line"
    _description = "Oil Gate Pass Line"

    gate_pass_id = fields.Many2one("oil.gate.pass", string="Gate Pass",
                                   required=True, ondelete="cascade",
                                   help="Select the gate Pass.")
    product_id = fields.Many2one("product.product", string="Product",
                                 required=True, help="Select the product.")
    quantity = fields.Float(string="Quantity", required=True, default=1.0,
                            help="Enter the quantity.")
    uom_id = fields.Many2one("uom.uom", string="UoM", required=True,
                             help="Select the uoM.")
