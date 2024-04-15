# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K(odoo@cybrosys.com)
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
##############################################################################
import datetime
from odoo import api, fields, models, _
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES


class WaterSupplyRequest(models.Model):
    """Model for water supply request form."""

    _name = "water.supply.request"
    _description = "Water Supply Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _date_name = "date_planned_start"
    _order = "priority desc, date_planned_start asc,id"
    _rec_name = "reference_no"

    @api.model
    def _get_default_date_planned_start(self):
        """Method returns the specified deadline date as a datetime object."""
        if self.env.context.get("default_date_deadline"):
            return fields.Datetime.to_datetime(
                self.env.context.get("default_date_deadline")
            )
        return datetime.datetime.now()

    reference_no = fields.Char(
        string="Sequence", readonly=True, default="New", help="Reference number"
    )
    responsible_user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        help="Responsible person",
    )
    customer_name_id = fields.Many2one(
        "res.partner",
        string="Customer Name",
        help="Name of the customer",
        required=True,
    )
    customer_email = fields.Char(
        related="customer_name_id.email", string="Customer Email", help="Customer email"
    )
    customer_phone = fields.Char(
        related="customer_name_id.phone",
        string="Customer Phone",
        help="Phone number of" " the customer.",
    )
    customer_address = fields.Char(
        related="customer_name_id.street",
        string="Customer Address",
        help="Customer address",
    )
    pickup_date = fields.Date(
        string="Pickup Date", help="Date of the pickup", required=True
    )
    request_date = fields.Date(
        string="Request Date", help="Date of the " "product request."
    )
    state = fields.Selection(
        [("draft", "Draft"), ("created", "Created"), ("supplied", "Supplied")],
        default="draft",
        string="State",
        help="State of the supply request.",
    )
    create_date = fields.Date(
        string="Create Date",
        default=fields.Date.today(),
        help="Create date of water supply request",
    )
    is_closed = fields.Boolean(
        string="Is Closed",
        help="Boolean field for to check the " "current request is closed or not",
    )
    date_planned_start = fields.Datetime(
        string="Scheduled Date",
        copy=False,
        default=_get_default_date_planned_start,
        help="Date at which you plan to start the production.",
        index=True,
        required=True,
    )
    supply_method_ids = fields.Many2many(
        "water.supply.methods",
        string="Supply Methods",
        help="Supply methods",
        required=True,
    )
    usage_categories_ids = fields.Many2many(
        "water.usage.categories",
        string="Usage Categories",
        help="Usage categories",
        required=True,
    )
    usage_place_id = fields.Many2one(
        "water.usage.places", string="Usage Place", help="Usage place", required=True
    )
    create_mo_ids = fields.One2many(
        "manufacturing.order.creation",
        "supply_request_id",
        string="Creation Manufacturing Order",
        help="Created manufacturing orders.",
    )
    mo_count = fields.Integer(
        string="Manufacture Order Count",
        compute="compute_mo_count",
        help="For storing manufacturing order count.",
    )
    stock_move_count = fields.Integer(
        string="Stock Move Count",
        compute="compute_stock_move_count",
        help="Store the stock move count.",
    )
    priority = fields.Selection(
        PROCUREMENT_PRIORITIES,
        string="Priority",
        default="0",
        help="Components will be reserved first for the MO "
        "with the highest priorities.",
    )

    @api.model_create_multi
    def create(self, vals):
        """Creating sequence number."""
        records = super(WaterSupplyRequest, self).create(vals)
        for record in records:
            if record.reference_no == _("New"):
                reference_no = self.env["ir.sequence"].next_by_code(
                    "water_supply_request"
                ) or _("New")
                record.write({"reference_no": reference_no})
        return records

    @api.onchange("supply_method_ids")
    def _onchange_supply_method_ids(self):
        """This method is triggered when the 'supply_method_ids' field is
        changed. It fills the 'create_mo_ids' many2many field with
        manufacturing order data based on the selected supply method's
        information."""
        self.create_mo_ids = False
        for record in self.supply_method_ids:
            product = self.env["product.product"].browse(record.created_product_id.id)
            bom = self.env["mrp.bom"].search([("product_id", "=", product.id)], limit=1)
            self.create_mo_ids = [
                fields.Command.create(
                    {
                        "product_id": product.id,
                        "quantity": bom.product_qty,
                        "uom_id": product.uom_id.id,
                        "bom_id": bom,
                    }
                )
            ]

    def action_apply(self):
        """Stock move will occur when supply the product to the customer."""
        self.write({"state": "created"})
        src_location = self.env["stock.location"].search(
            [("usage", "=", "internal"), ("name", "=", "Stock")], limit=1
        )
        dest_location = self.env["stock.location"].search(
            [("usage", "=", "customer")], limit=1
        )
        for rec in self.create_mo_ids:
            move = self.env["stock.move"].create(
                {
                    "name": self.reference_no,
                    "origin": self.reference_no,
                    "location_id": src_location.id,
                    "location_dest_id": dest_location.id,
                    "product_id": rec.product_id.id,
                    "product_uom": rec.product_id.uom_id.id,
                    "product_uom_qty": rec.quantity,
                    "supply_id": self.id,
                }
            )
            move.write({"state": "done"})
            manufacturing_order = self.env["mrp.production"].search(
                [("name", "=", self.create_mo_ids.mrp_id.mapped("name"))]
            )
            manufacturing_order.write({"supply_id": self})

    def action_supply(self):
        """Enabling the boolean field if the request is supplied."""
        self.write({"state": "supplied"})
        if self.state == "supplied":
            self.is_closed = True

    def action_stock_move(self):
        """Opens a window displaying stock moves related to the current
        record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Stock Move",
            "view_mode": "tree,form",
            "res_model": "stock.move",
            "domain": [("supply_id", "=", self.id)],
        }

    def action_mrp_production(self):
        """Display the production records associated with the current supply
        order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Manufacturing Order",
            "view_mode": "tree,form",
            "res_model": "mrp.production",
            "domain": [("supply_id", "=", self.id)],
        }

    def compute_mo_count(self):
        """This method calculates the number of manufacturing orders
        associated with the current record and updates the 'mo_count'
        field on each record accordingly."""
        for record in self:
            record.mo_count = self.env["mrp.production"].search_count(
                [("supply_id", "=", self.id)]
            )

    def compute_stock_move_count(self):
        """This method iterates through the records in `self` and calculates
        the number of stock moves associated with each record. It sets the
        `stock_move_count` field of each record to the corresponding count."""
        for record in self:
            record.stock_move_count = self.env["stock.move"].search_count(
                [("supply_id", "=", self.id)]
            )
