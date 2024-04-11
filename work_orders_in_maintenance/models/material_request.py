# -*- coding: utf-8 -*-
# ###############################################################################
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
from odoo import api, fields, models


class MaterialRequest(models.Model):
    """Model for managing Maintenance
    Requests. This class extends the base 'maintenance.request'
    model to include the ability to create work orders.
    """

    _name = "material.request"

    name = fields.Char("Name", help="Purchase order for the item.")
    equipment_id = fields.Many2one(
        "maintenance.equipment", "Equipment", help="Select the Equipment."
    )
    product_qty = fields.Float("Quantity", help="Enter the quantity of the Equipment.")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("received", "Received"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        required=True,
        copy=False,
        tracking=True,
        default="in_progress",
        help="Choose the status of the item: Draft, In Progress, Received, or Cancelled.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
        help="Select the associated company.",
    )
    maintenance_request_id = fields.Many2one(
        "maintenance.request", help="Select the associated maintenance request."
    )
    is_product_received = fields.Boolean(compute="_compute_is_product_received")

    def _compute_is_product_received(self):
        """
        Compute method to determine if any line in the recordset has the state set to 'received'.
        Sets the 'is_product_received' field accordingly.
        """
        for record in self:
            record.is_product_received = any(
                line.state == "received" for line in record
            )

    @api.model
    def create(self, vals):
        """Create the sequence for the Material Request."""
        res = super(MaterialRequest, self).create(vals)
        if vals.get("name", "New") == "New":
            res.name = (
                self.env["ir.sequence"].next_by_code("material.request.id") or "New"
            )
        return res

    def action_receive(self):
        """Change the state of the material request  to 'received'.This function
        updates the state of the order to 'done' to indicate that
        the order is completed."""
        self.state = "received"

    def action_cancel(self):
        """Change the state of the material request to 'cancelled'.This function
        updates the state of the material request to 'cancelled' to indicate that
        the material request is cancelled."""
        self.state = "cancel"
