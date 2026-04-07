# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import json
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleReservation(WebsiteSale):
    """Custom controller for handling reservation-related functionality on
    the website."""

    @http.route(
        ["/reservation", "/reservation/page/<int:page>"],
        type="http",
        auth="public",
        website=True,
    )
    def reservation(self, page=1):
        """Display a page with products available for reservation.
        :param page: Page number for pagination.
        :param kw: Additional keyword arguments.
        :return: HTTP response rendering the reservation page."""
        domain = [("reserve_products", "=", True), ("website_published", "=", True)]
        product_obj = request.env["product.template"]
        product_count = product_obj.search_count(domain)
        pager = request.website.pager(
            url="/reservation", total=product_count, page=page, step=12
        )
        products = product_obj.search(domain, limit=12, offset=pager["offset"])
        values = {
            "products": products,
            "page_name": "Reserve Products",
            "pager": pager,
            "default_url": "/reservation",
        }
        if request.cart:
            request.cart.order_line.unlink()
        return request.render("website_product_reservation.reservation_page", values)

    @http.route(
        ["/reservation/reserve"],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def reservation_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """Update the reservation order based on user input.
        :param product_id: ID of the product being reserved.
        :param add_qty: Quantity to add to the reservation.
        :param set_qty: Quantity to set for the reservation.
        :param kw: Additional keyword arguments.
        :return: HTTP response redirecting to the shopping cart."""
        product_custom_attribute_values = None
        if kw.get("product_custom_attribute_values"):
            product_custom_attribute_values = json.loads(
                kw.get("product_custom_attribute_values")
            )
        order = request.cart if request.cart else request.website._create_cart()
        
        if float(set_qty):
            line = order.order_line.filtered(lambda l: l.product_id.id == int(product_id))[:1]
            if line:
                order._cart_update_line_quantity(
                    line_id=line.id,
                    quantity=float(set_qty),
                    product_custom_attribute_values=product_custom_attribute_values,
                )
            else:
                order._cart_add(
                    product_id=int(product_id),
                    quantity=float(set_qty),
                    product_custom_attribute_values=product_custom_attribute_values,
                )
        elif float(add_qty):
            order._cart_add(
                product_id=int(product_id),
                quantity=float(add_qty),
                product_custom_attribute_values=product_custom_attribute_values,
            )
        
        if kw.get("type_name") == "Reservation":
            order.is_reservation_order = True
        return request.redirect("/shop/cart")

    @http.route(
        ["/reservation/confirm_reserve_order"], type="http", auth="public", website=True
    )
    def confirm_reserve_order(self):
        """Confirm and finalize the reservation order.
        :param post: POST data from the request.
        :return: HTTP response rendering the confirmation or error page."""
        order = request.cart
        if not order:
            return request.redirect("/shop")
        is_reservation = all(
            order.website_order_line.mapped("product_id").mapped("reserve_products")
        )
        if is_reservation:
            order.state = "reserve"
            request.website.sale_reset()
            for line in order.order_line.filtered(
                lambda line: line.product_id.type == "product"
            ):
                line.sudo().create_reservation_stock()
            # Store the order ID in the session before resetting the cart
            request.session['sale_last_order_id'] = order.id
            # Explicitly force session modification and ensure reset
            request.website.sale_reset()
            return request.redirect("/reservation/thankyou")
        return request.render(
            "website_product_reservation.not_allowed_to_reserve_page", {}
        )

    @http.route(
        ["/reservation/thankyou"],
        type="http",
        auth="public",
        website=True,
        sitemap=False
    )
    def reservation_thankyou(self):
        """Render the thank you page for reservation orders."""
        order_id = request.session.get('sale_last_order_id')
        # Verify current cart status
        if order_id:
            order = request.env['sale.order'].sudo().browse(order_id)
            return request.render(
                "website_product_reservation.reservation_thankyou", {"order": order}
            )
        return request.redirect("/shop")
