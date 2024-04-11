# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (odoo@cybrosys.com)
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
#
###############################################################################
from datetime import datetime
from odoo import api, fields, models


class MaintenanceWork(models.Model):
    """
    This class represents Maintenance Work in the system.

    Maintenance Work includes tasks related to equipment maintenance, such as
    repairs, inspections, and other maintenance activities."""

    _name = "maintenance.work"
    _description = "Maintenance Work"

    name = fields.Char("Name", help="Name of the maintenance work.")
    technician_id = fields.Many2one(
        "res.users",
        "Technician",
        help="Select the technician responsible for the work.",
    )
    maintenance_request_id = fields.Many2one(
        "maintenance.request", help="Related maintenance request."
    )
    work_center_id = fields.Many2one(
        "mrp.workcenter", help="Work center associated with the work."
    )
    schedule_date_start = fields.Date(
        "Scheduled Date", help="Scheduled start date for the work."
    )
    duration = fields.Float(
        "Duration", help="Estimated duration for the work in hours."
    )
    equipment_id = fields.Many2one(
        "maintenance.equipment", help="Equipment associated with the work."
    )
    partner_id = fields.Many2one(
        "res.partner", help="The related partner associated with this record."
    )
    maintenance_id = fields.Integer(
        string="Maintenance", help="Identifier for maintenance purposes."
    )
    description = fields.Text(
        string="Description",
        help="Additional details or a brief description of the record.",
    )
    invoice_count = fields.Integer(compute="_compute_invoice_count")
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

    def _compute_invoice_count(self):
        """To compute the invoice counts."""
        for record in self:
            invoice_count = self.env["account.move"].search_count(
                [("maintenance_request_id", "=", record.maintenance_request_id.id)]
            )
            record.invoice_count = invoice_count

    @api.model
    def create(self, vals):
        """
        Override of the create method to customize the creation process for MaintenanceWork.

        :param vals: Dictionary of values for creating the record.
        :return: Newly created record.
        """
        res = super(MaintenanceWork, self).create(vals)
        if vals.get("name", "New") == "New":
            res.name = self.env["ir.sequence"].next_by_code("work.order.id") or "New"
        return res

    def action_confirm(self):
        """Change the state of the order to 'progress'.This function
        updates the state of the order to 'ready' to indicate that
        the order is confirmed and ready for further processing."""
        self.state = "progress"

    def action_complete_order(self):
        """Change the state of the order to 'done'.This function
        updates the state of the order to 'done' to indicate that
        the order is completed."""
        self.state = "done"
        self.maintenance_request_id.stage_id = self.env.ref("maintenance.stage_3").id

    def action_cancel(self):
        """Change the state of the order to 'cancelled'.This function
        updates the state of the order to 'cancelled' to indicate that
        the order is cancelled."""
        self.state = "cancelled"

    def action_create_invoice(self):
        """Function to create the invoice."""
        self.state = "invoice"
        maintenance_invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "invoice_date": datetime.now(),
                "partner_id": self.partner_id.id,
                "maintenance_request_id": self.maintenance_request_id.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.maintenance_request_id.name,
                        },
                    )
                ],
            }
        )
        self.maintenance_id = maintenance_invoice.id
        return {
            "name": "Invoice Maintenance Work Order",
            "res_model": "account.move",
            "res_id": maintenance_invoice.id,
            "view_mode": "form",
            "type": "ir.actions.act_window",
        }

    def invoice_details(self):
        """The Invoice details to display."""
        return {
            "name": "Invoices",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "domain": [("maintenance_request_id", "=", self.maintenance_request_id.id)],
        }
