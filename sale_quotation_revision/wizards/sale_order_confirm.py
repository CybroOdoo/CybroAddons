# -*- coding: utf-8 -*-
#############################################################################
#
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
from odoo import models, fields


class SaleOrderConfirmWizard(models.TransientModel):
    _name = "sale.order.confirm.wizard"
    _description = "Confirm Sale Order Wizard"

    order_id = fields.Many2one(
        "sale.order",
        string="Sale Order to Confirm",
        help="Select the sale orders to be conform.",
    )
    sale_orders_ids = fields.Many2many(
        "sale.order",
        string="Sale Order to Cancel",
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
