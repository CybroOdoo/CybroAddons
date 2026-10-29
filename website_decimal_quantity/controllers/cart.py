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
#############################################################################
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.website_sale.controllers.cart import Cart


class CartDecimal(Cart):
    """Controller class to handle HTTP routes."""

    @http.route()
    def add_to_cart(
        self,
        product_template_id,
        product_id,
        quantity,
        uom_id=None,
        product_custom_attribute_values=None,
        no_variant_attribute_value_ids=None,
        linked_products=None,
        **kwargs,
    ):
        """Add a product to the shopping cart supporting float quantities."""
        order_sudo = request.cart or self.env.website._create_cart()
        quantity = (quantity and float(quantity)) or 1.0
        product = self.env["product.product"].browse(product_id).exists()
        if product and no_variant_attribute_value_ids:
            product = product.with_context(
                **product._get_product_price_context(
                    self.env["product.template.attribute.value"].browse([
                        int(v) for v in no_variant_attribute_value_ids
                    ])
                )
            )
        if not product or not product._is_add_to_cart_allowed():
            raise UserError(
                self.env._("The given product does not exist therefore it cannot be added to cart.")
            )
        added_qty_per_line = {}
        values = order_sudo.with_context(skip_cart_verification=True)._cart_add(
            product_id=product_id,
            quantity=quantity,
            uom_id=uom_id,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids,
            **kwargs,
        )
        line_ids = {product_template_id: values["line_id"]}
        added_qty_per_line[values["line_id"]] = values["added_qty"]
        tracking_info = values.get("tracking_info", [])
        is_combo = product.type == "combo"
        updated_line = (
            values["line_id"]
            and order_sudo.order_line.filtered(lambda line: line.id == values["line_id"])
        ) or order_sudo.env["sale.order.line"]
        if linked_products and values["line_id"]:
            for product_data in linked_products:
                product_sudo = (
                    self.env["product.product"].sudo().browse(product_data["product_id"]).exists()
                )
                if product_data["quantity"] and (
                    not product_sudo
                    or (
                        not product_sudo._is_add_to_cart_allowed()
                        and not product_data.get("combo_item_id")
                    )
                ):
                    raise UserError(
                        self.env._(
                            "The given product does not exist therefore it cannot be added to cart."
                        )
                    )
                product_values = order_sudo.with_context(skip_cart_verification=True)._cart_add(
                    product_id=product_data["product_id"],
                    quantity=float(product_data["quantity"]),
                    uom_id=product_data.get("uom_id"),
                    product_custom_attribute_values=product_data["product_custom_attribute_values"],
                    no_variant_attribute_value_ids=[
                        int(value_id) for value_id in product_data["no_variant_attribute_value_ids"]
                    ],
                    linked_line_id=line_ids[product_data["parent_product_template_id"]],
                    **self._get_additional_cart_update_values(product_data),
                    **kwargs,
                )
                if is_combo and not product_values.get("quantity"):
                    updated_line.unlink()
                    return {
                        "cart_quantity": order_sudo.cart_quantity,
                        "notifications": [
                            {
                                "type": "warning",
                                "data": {"warning_message": product_values.get("warning", "")},
                            }
                        ],
                        "quantity": 0,
                        "tracking_info": [],
                    }
                line_ids[product_data["product_template_id"]] = product_values["line_id"]
                added_qty_per_line[product_values["line_id"]] = product_values["added_qty"]
                tracking_info += product_values.get("tracking_info", [])
        warning = values.pop("warning", "")
        if is_combo and (changed_reason := order_sudo._check_combo_quantities(updated_line)):
            added_qty_per_line = {
                line.id: updated_line.product_uom_qty
                for line in (updated_line + updated_line.linked_line_ids)
            }
            warning = changed_reason
            values["quantity"] = updated_line.product_uom_qty
        order_sudo._verify_cart_after_update()
        main_product_line = self.env["sale.order.line"].browse(values["line_id"])
        if main_product_line.product_type == "combo":
            main_product_line._check_validity()
        positive_added_qty_per_line = {
            line_id: qty for line_id, qty in added_qty_per_line.items() if qty > 0
        }
        notifications = []
        if notification := self._get_cart_notification_information(
            order_sudo, positive_added_qty_per_line
        ):
            notifications.append({"type": "item_added", "data": notification})
        if warning:
            (updated_line or order_sudo)._add_warning_alert(warning)
            notifications.append({"type": "warning", "data": {"warning_message": warning}})
        return {
            "cart_quantity": order_sudo.cart_quantity,
            "notifications": notifications,
            "quantity": values.pop("quantity", 0),
            "tracking_info": tracking_info,
            "currency": order_sudo.currency_id.name,
        }

    @http.route()
    def update_cart(self, line_id, quantity, product_id=None, **kwargs):
        """Update the quantity of a specific line allowing float values."""
        order_sudo = request.cart
        quantity = float(quantity)
        if not line_id:
            line_id = order_sudo.order_line.filtered(lambda sol: sol.product_id.id == product_id)[
                :1
            ].id
        values = order_sudo._cart_update_line_quantity(line_id, quantity, **kwargs)
        values.update(self._get_updated_cart_page_values(order_sudo))
        values["website_sale.quick_reorder_history"] = self.env.website._render_template(
            "website_sale.quick_reorder_history",
            {"website_sale_order": order_sudo, **self._prepare_order_history()},
        )
        return values
