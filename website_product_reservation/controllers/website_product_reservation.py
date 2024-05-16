# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
    def reservation(self, page=1, **kw):
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
        self.clear_cart()
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
        request.website.sale_get_order(force_create=1)._cart_update(
            product_id=int(product_id),
            add_qty=float(add_qty),
            set_qty=float(set_qty),
            product_custom_attribute_values=product_custom_attribute_values,
        )
        if kw.get("type_name") == "Reservation":
            request.website.sale_get_order().is_reservation_order = True
        return request.redirect("/shop/cart")

    @http.route(
        ["/reservation/confirm_reserve_order"], type="http", auth="public", website=True
    )
    def confirm_reserve_order(self, **post):
        """Confirm and finalize the reservation order.
        :param post: POST data from the request.
        :return: HTTP response rendering the confirmation or error page."""
        order = request.website.sale_get_order()
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
            self.clear_cart()
            return request.render(
                "website_product_reservation.reservation_thankyou", {"order": order}
            )
        else:
            return request.render(
                "website_product_reservation.not_allowed_to_reserve_page", {}
            )
