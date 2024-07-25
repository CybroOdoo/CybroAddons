# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raneesha MK (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ServiceBooking(models.Model):
    """Class to add car service booking"""
    _name = "service.booking"
    _inherit = "mail.thread", "mail.activity.mixin"
    _description = "Service Booking"
    _rec_name = "reference_no"

    reference_no = fields.Char(
        string="Order Reference",
        readonly=True,
        copy=False,
        default=lambda self: _("New"),
        help="This field represents the reference number of the order.")
    vehicle_no = fields.Char(string="Vehicle Number", required=True,
                             help="Enter vehicle number")
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True,
        help="Select Customer name")
    number = fields.Char(string="Mobile No", help="Enter your Mobile Number")
    model_id = fields.Many2one(
        comodel_name="fleet.vehicle.model",
        string="Vehicle Model",
        domain=[("vehicle_type", "=", "car")],
        required=True,
        help="Select your Car Model")
    date = fields.Date(string="Date", required=True, help="Service Date")
    service_package_id = fields.Many2one(
        "service.package",
        string="Service Package",
        required=True,
        help="Select service Package")
    service_package_price = fields.Monetary(
        string="Amount",
        related="service_package_id.total",
        help="Service type total amount")
    location = fields.Char(string="Location",
                           help="Enter your Current location")
    special_instruction = fields.Text(
        string="Any Special Instructions",
        help="If you have any special " "instruction add")
    task_count = fields.Integer(
        string="Task",
        compute="compute_task_count",
        help="This field represents the number of tasks associated with this "
             "record.")
    service_worksheet_ids = fields.One2many(
        "service.worksheet",
        "service_booking_id",
        string="Worksheet",
        help="Service worksheets related to this service booking.")
    invoice_count = fields.Integer(
        string="Invoice Count",
        compute="compute_invoice_count",
        help="Number of invoices associated with " "this record.")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id.id,
        help="Select the company to which this record " "belongs.")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        help="The currency used by the company.")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("to_invoice", "To Invoice"),
            ("invoice", "Invoice")],
        string="State", default="draft",
        help="State of the record: Draft, Confirm, or " "Invoice.")

    def compute_task_count(self):
        """Function to calculate task count"""
        for vehicle in self:
            vehicle.task_count = vehicle.env["service.worksheet"].search_count(
                [("service_booking_id", "=", self.id)])

    def action_view_worksheet(self):
        """smart button to view the corresponding worksheet of service
        booking"""
        return {
            "type": "ir.actions.act_window",
            "name": "Worksheet",
            "view_mode": "tree,form",
            "res_model": "service.worksheet",
            "target": "current",
            "domain": [("service_booking_id", "=", self.id)],
            "context": {"create": False},
        }

    @api.model
    def create(self, vals):
        """function to create sequence"""
        if vals.get("reference_no", _("New")) == _("New"):
            vals["reference_no"] = self.env["ir.sequence"].next_by_code(
                "service.booking"
            ) or _("New")
        return super(ServiceBooking, self).create(vals)

    def action_confirm(self):
        """function to create worksheet for the service"""
        self.write({"state": "confirm"})
        for service_type_id in self.service_package_id.service_ids.service_type_id:
            self.env["service.worksheet"].create(
                {
                    "model_id": self.model_id.id,
                    "service_type_id": service_type_id.id,
                    "service_booking_id": self.id,
                    "user_id": self.env.user.id,
                }
            )

    def action_create_invoice(self):
        """Function to create invoice"""
        self.write({"state": "to_invoice"})
        invoiced_amount = sum(
            self.env["account.move"]
            .search(
                [("invoice_origin", "=", self.reference_no),
                 ("state", "!=", "cancel")]
            )
            .mapped("amount_untaxed_signed"))
        invoice = self.env["account.move"].create(
            [
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner_id.id,
                    "invoice_origin": self.reference_no,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "{} / {} / Service Package: {}".format(
                                    self.model_id.name,
                                    self.vehicle_no,
                                    self.service_package_id.name,
                                ),
                                "quantity": 1,
                                "price_unit": self.service_package_price
                                              - invoiced_amount,
                                "price_subtotal": self.service_package_price
                                                  - invoiced_amount,
                            },
                        )
                    ],
                }
            ]
        )
        return {
            "name": "invoice",
            "view_mode": "form",
            "res_id": invoice.id,
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def compute_invoice_count(self):
        """function to count invoice"""
        for record in self:
            record.invoice_count = self.env["account.move"].search_count(
                [("invoice_origin", "=", self.reference_no)]
            )

    def action_view_invoice(self):
        """Action method to view invoices related to the current record.
        :return: Action dictionary"""
        return {
            "type": "ir.actions.act_window",
            "name": "Invoice",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "target": "current",
            "domain": [("invoice_origin", "=", self.reference_no)],
            "context": {"create": False},
        }

    def unlink(self):
        """Inherit the 'unlink' method to prevent the deletion of confirmed or
        invoiced records.
        This method ensures that records in the 'confirmed' or 'invoiced' state
        cannot be deleted.
        If any of the selected records are in these states, it raises a user
        error to prevent deletion.
        :raises UserError: If any record is in the 'confirmed' or 'invoiced'
        state, preventing deletion.
        :return: Result of the 'unlink' method"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(
                    _("You can not delete a confirmed or a Invoiced service booking.")
                )
        return super().unlink()
