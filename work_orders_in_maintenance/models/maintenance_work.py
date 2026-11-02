# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo import api, fields, models


class MaintenanceWork(models.Model):
    """Maintenance work order.

    A work order tracks the repair, inspection or other maintenance activity
    carried out for a maintenance request, and can be invoiced.
    """

    _name = "maintenance.work"
    _description = "Maintenance Work"
    _inherit = ["mail.thread"]
    _order = "id desc"

    name = fields.Char(
        default="New",
        readonly=True,
        copy=False,
        help="Reference of the maintenance work.",
    )
    technician_id = fields.Many2one(
        "res.users",
        help="Select the technician responsible for the work.",
    )
    maintenance_request_id = fields.Many2one(
        "maintenance.request",
        help="Related maintenance request.",
    )
    work_center_id = fields.Many2one(
        "mrp.workcenter",
        help="Work center associated with the work.",
    )
    schedule_date_start = fields.Date(
        string="Scheduled Date", help="Scheduled start date for the work."
    )
    duration = fields.Float(
        help="Estimated duration for the work in hours."
    )
    equipment_id = fields.Many2one(
        "maintenance.equipment",
        help="Equipment associated with the work.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        help="Customer invoiced for this work.",
    )
    invoice_id = fields.Many2one(
        "account.move",
        copy=False,
        readonly=True,
        help="Invoice created for this work order.",
    )
    description = fields.Text(
        help="Additional details or a brief description of the work.",
    )
    invoice_count = fields.Integer(
        string="Invoices",
        compute="_compute_invoice_count",
        help="Number of invoices linked to the maintenance request.",
    )
    state = fields.Selection(
        [
            ("ready", "Ready"),
            ("progress", "In Progress"),
            ("done", "Finished"),
            ("invoice", "Invoiced"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="ready",
        help="Choose the status of the maintenance work.",
    )

    @api.depends("maintenance_request_id", "invoice_id")
    def _compute_invoice_count(self):
        """Compute the number of invoices of the maintenance request."""
        move_model = self.env["account.move"].sudo()
        for record in self:
            record.invoice_count = move_model.search_count(
                [("maintenance_request_id", "=", record.maintenance_request_id.id)]
            ) if record.maintenance_request_id else 0

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the work order sequence on creation."""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("work.order.id") or "New"
                )
        return super().create(vals_list)

    def action_confirm(self):
        """Move the work order to 'In Progress'."""
        self.write({"state": "progress"})

    def action_complete_order(self):
        """Mark the work order as finished and the request as repaired."""
        self.write({"state": "done"})
        stage = self.env.ref("maintenance.stage_3", raise_if_not_found=False)
        if stage:
            self.maintenance_request_id.write({"stage_id": stage.id})

    def action_cancel(self):
        """Cancel the work order."""
        self.write({"state": "cancelled"})

    def action_create_invoice(self):
        """Create the customer invoice of the work order and open it."""
        self.ensure_one()
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "invoice_date": fields.Date.context_today(self),
                "partner_id": self.partner_id.id,
                "maintenance_request_id": self.maintenance_request_id.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.maintenance_request_id.name or self.name,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )
        self.write({"state": "invoice", "invoice_id": invoice.id})
        return {
            "name": self.env._("Invoice Maintenance Work Order"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "type": "ir.actions.act_window",
        }

    def invoice_details(self):
        """Open the invoices linked to the maintenance request."""
        self.ensure_one()
        return {
            "name": self.env._("Invoices"),
            "view_mode": "list,form",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "domain": [("maintenance_request_id", "=", self.maintenance_request_id.id)],
        }
