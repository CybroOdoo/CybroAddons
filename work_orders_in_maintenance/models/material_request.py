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


class MaterialRequest(models.Model):
    """Material request raised from a maintenance request."""

    _name = "material.request"
    _description = "Material Request"
    _inherit = ["mail.thread"]
    _order = "id desc"

    name = fields.Char(
        default="New",
        readonly=True,
        copy=False,
        help="Reference of the material request.",
    )
    equipment_id = fields.Many2one(
        "maintenance.equipment", help="Select the Equipment."
    )
    product_qty = fields.Float(
        string="Quantity", help="Enter the quantity of the Equipment."
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("received", "Received"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="in_progress",
        help="Choose the status of the item: Draft, In Progress, Received, "
        "or Cancelled.",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
        help="Select the associated company.",
    )
    maintenance_request_id = fields.Many2one(
        "maintenance.request",
        help="Select the associated maintenance request.",
    )
    is_product_received = fields.Boolean(
        string="Product Received",
        compute="_compute_is_product_received",
        help="Set when the material request is received.",
    )

    @api.depends("state")
    def _compute_is_product_received(self):
        """Flag the requests whose state is 'received'."""
        for record in self:
            record.is_product_received = record.state == "received"

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the material request sequence on creation."""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("material.request.id")
                    or "New"
                )
        return super().create(vals_list)

    def action_receive(self):
        """Mark the material request as received."""
        self.write({"state": "received"})

    def action_cancel(self):
        """Cancel the material request."""
        self.write({"state": "cancel"})
