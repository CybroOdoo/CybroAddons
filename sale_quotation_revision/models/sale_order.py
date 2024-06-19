# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Inheriting the sale order model to add the fields
    and revise quotation button"""

    _inherit = "sale.order"

    is_revised = fields.Boolean(
        string="Is Revised", copy=False, help="Is Order Revised"
    )
    org_sale_id = fields.Many2one(
        "sale.order", string="Origin", copy=False, help="Revised Order Origin"
    )
    rev_sale_ids = fields.One2many(
        "sale.order",
        "org_sale_id",
        string="Sales Revisions",
        copy=False,
        help="Revised Sale Orders",
    )
    rev_ord_count = fields.Integer(
        string="Revised Orders",
        help="Revised order count",
        compute="compute_rev_ord_count",
    )
    rev_confirm = fields.Boolean(
        string="Revised Confirm", copy=False, help="Is Revised Confirm"
    )

    def action_revise_quotation(self):
        """Revise the current quotation."""
        revise_name = str(self.name) + "/R" + str(len(self.rev_sale_ids) + 1)
        vals = {"name": revise_name, "org_sale_id": self.id}
        revise_quote = self.copy(default=vals)
        self.is_revised = True
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "sale.order",
            "views": [(False, "form")],
            "res_id": revise_quote.id,
        }

    def compute_rev_ord_count(self):
        """Compute the number of revised order of the current order."""
        for record in self:
            record.rev_ord_count = len(record.rev_sale_ids)

    def get_revised_orders(self):
        """Action to open the revised order of the current order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Revised Order",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "domain": [("org_sale_id", "=", self.id)],
            "context": "{'create': False}",
        }

    def unlink(self):
        """Override the unlink method to restrict deletion of
        original sale order."""
        for order in self:
            if order.is_revised and order.rev_ord_count > 0:
                raise UserError(
                    "Cannot delete a sale order with revised orders."
                    " Please delete the revised orders first."
                )
        return super(SaleOrder, self).unlink()

    def action_confirm(self):
        """Override the action_confirm method to handle revised orders."""
        for order in self:
            if not order.rev_confirm:
                related_orders = order.get_related_orders(order)
                if related_orders:
                    # Exclude the original sale order from the list
                    related_orders -= order
                    wizard = self.env["sale.order.confirm.wizard"].create(
                        {
                            "order_id": order.id,
                            "sale_orders_ids": [(6, 0, related_orders.ids)],
                        }
                    )
                    return {
                        "name": "Confirm Related Sale Orders",
                        "type": "ir.actions.act_window",
                        "view_mode": "form",
                        "res_model": "sale.order.confirm.wizard",
                        "res_id": wizard.id,
                        "target": "new",
                    }
            super(SaleOrder, order).action_confirm()

    def get_related_orders(self, order):
        """Get related sale orders."""
        related_orders = order.rev_sale_ids.filtered(
            lambda r: r.state not in ["cancel", "sale"]
        )
        if order.org_sale_id:
            if order.org_sale_id.state not in ["cancel", "sale"]:
                related_orders += order.org_sale_id
            # Add related sale orders of order.org_sale_id
            org_related_orders = order.org_sale_id.rev_sale_ids.filtered(
                lambda r: r.state not in ["cancel", "sale"]
            )
            related_orders += org_related_orders
        return related_orders


class SaleOrderConfirmWizard(models.TransientModel):
    _name = "sale.order.confirm.wizard"
    _description = "Confirm Sale Order Wizard"

    order_id = fields.Many2one(
        "sale.order",
        string="Sale Orders to Confirm",
        help="Select the sale orders to be conform.",
    )
    sale_orders_ids = fields.Many2many(
        "sale.order",
        string="Sale Orders to Cancel",
        help="Select the sale orders to be canceled.",
    )

    def action_rev_cancel_orders(self):
        """Method to confirm or cancel selected sale orders."""
        for wizard in self:
            wizard.order_id.rev_confirm = True
            wizard.order_id.action_confirm()
            for order in wizard.sale_orders_ids:
                order._action_cancel()
        return {"type": "ir.actions.act_window_close"}

    def action_rev_keep_orders(self):
        """Method to keep related sale orders."""
        for wizard in self:
            wizard.order_id.rev_confirm = True
            wizard.order_id.action_confirm()
        return {"type": "ir.actions.act_window_close"}
